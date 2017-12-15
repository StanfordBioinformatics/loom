import os
import re
import shutil
import tempfile
import unittest
from loomengine_utils import file_utils

SAMPLE_GOOGLE_STORAGE_BUCKET = 'gs://genomics-public-data'
SAMPLE_GOOGLE_STORAGE_FILE = 'gs://genomics-public-data/'\
                             '1000-genomes/other/sample_info/'\
                             'sample_info.schema'

class TestUrlParse(unittest.TestCase):

    def testValidateUrlWithRemoteHost(self):
        path = 'file://remotehost/path/file'
        with self.assertRaises(file_utils.UrlValidationError):
            file_utils._urlparse(path)

    def testValidateWithUnsupportedScheme(self):
        path = 'tcp:///path/file'
        with self.assertRaises(file_utils.UrlValidationError):
            file_utils._urlparse(path)

    def testUrlParseWithImplicitFileScheme(self):
        path = '/path/file'
        url = file_utils._urlparse(path)
        self.assertEqual(url.scheme, 'file')
        self.assertEqual(url.path, path)


class TestFileSet(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.filenames = ['file0.txt', 'file1.txt', 'file2.txt']
        self.filepaths = []
        for filename in self.filenames:
            filepath = os.path.join(self.tempdir, filename)
            self.filepaths.append(filepath)
            with open(filepath, 'w') as f:
                f.write(filename)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def testMixedPatterns(self):
        local_pattern = os.path.join(self.tempdir, 'file*.txt')
        gs_pattern = SAMPLE_GOOGLE_STORAGE_FILE
        settings = {'GCE_PROJECT': ''}
        file_set = file_utils.FileSet(
            [local_pattern, gs_pattern], settings)
        files = [file.get_url() for file in file_set]
        self.assertEqual(len(files), 4)
        self.assertTrue(SAMPLE_GOOGLE_STORAGE_FILE in files)


class TestFilePatternFactory(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.filename = 'file0.txt'
        self.filepath = os.path.join(self.tempdir, self.filename)
        with open(self.filepath, 'w') as f:
            f.write(self.filename)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def testFactoryGoogleStorageFilePattern(self):
        pattern = SAMPLE_GOOGLE_STORAGE_FILE
        settings = {'GCE_PROJECT': ''}
        file_pattern = file_utils.FilePattern(pattern, settings, retry=False)
        self.assertTrue(
            isinstance(file_pattern, file_utils.GoogleStorageFilePattern))

    def testFactoryLocalFilePattern(self):
        pattern = 'file://'+self.filepath
        settings = {}
        file_pattern = file_utils.FilePattern(pattern, settings, retry=False)
        self.assertTrue(isinstance(file_pattern, file_utils.LocalFilePattern))

    def testFactoryLocalFilePatternNoProtocol(self):
        pattern = self.filepath
        settings = {}
        file_pattern = file_utils.FilePattern(pattern, settings, retry=False)
        self.assertTrue(isinstance(file_pattern, file_utils.LocalFilePattern))


class TestGoogleStorageFilePattern(unittest.TestCase):

    def testInit(self):
        pattern = SAMPLE_GOOGLE_STORAGE_FILE
        settings = {'GCE_PROJECT': ''}
        file_pattern = file_utils.GoogleStorageFilePattern(
            pattern, settings, retry=False)
        files = [file for file in file_pattern]
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].url.geturl(), SAMPLE_GOOGLE_STORAGE_FILE)
    
    def testInitMissingFile(self):
        pattern = SAMPLE_GOOGLE_STORAGE_FILE+'thisfiledoesntexist'
        settings = {'GCE_PROJECT': ''}
        file_pattern = file_utils.GoogleStorageFilePattern(
            pattern, settings, retry=False)
        files = [file for file in file_pattern]
        self.assertEqual(len(files), 0)


class TestLocalFilePattern(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.filenames = ['file0.txt', 'file1.txt',
                          'file1.txt.metadata.yaml', 'file2.txt.metadata.yaml']
        self.filepaths = []
        for filename in self.filenames:
            filepath = os.path.join(self.tempdir, filename)
            self.filepaths.append(filepath)
            with open(filepath, 'w') as f:
                f.write(filename)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def testInit(self):
        pattern = 'file://'+os.path.join(self.tempdir, 'file0.txt')
        settings = {}
        file_pattern = file_utils.FilePattern(pattern, settings, retry=False)
        files = [file for file in file_pattern]
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].url.geturl(), 'file://'+self.filepaths[0])

    def testInitNoScheme(self):
        pattern = os.path.join(self.tempdir, 'file0.txt')
        settings = {}
        file_pattern = file_utils.FilePattern(pattern, settings, retry=False)
        files = [file for file in file_pattern]
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].url.geturl(), 'file://'+self.filepaths[0])

    def testWildcard(self):
        pattern = 'file://'+os.path.join(self.tempdir, 'file?.txt')
        settings = {}
        file_pattern = file_utils.FilePattern(pattern, settings, retry=False)
        files = [file for file in file_pattern]
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].get_url(), 'file://'+self.filepaths[0])
        self.assertEqual(files[1].get_url(), 'file://'+self.filepaths[1])

    def testTrimMetadataSuffix(self):
        pattern = 'file://'+os.path.join(self.tempdir, 'file?.txt*')
        settings = {}
        file_set = file_utils.FileSet([pattern], settings, retry=False,
                                              trim_metadata_suffix=True)
        files = [file for file in file_set]
        self.assertEqual(len(files), 3)
        self.assertEqual(files[0].get_url(), 'file://'+self.filepaths[0])
        self.assertEqual(files[1].get_url(), 'file://'+self.filepaths[1])
        self.assertEqual(files[2].get_url()+'.metadata.yaml',
                         'file://'+self.filepaths[3])
        

class TestFile(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.filename = 'file0.txt'
        self.filepath = os.path.join(self.tempdir, self.filename)
        with open(self.filepath, 'w') as f:
            f.write(self.filename)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def testFactoryGoogleStorageFile(self):
        url = SAMPLE_GOOGLE_STORAGE_FILE
        settings = {'GCE_PROJECT': ''}
        file = file_utils.File(url, settings, retry=False)
        self.assertTrue(isinstance(file, file_utils.GoogleStorageFile))

    def testFactoryLocalFile(self):
        url = 'file://'+self.filepath
        settings = {}
        file = file_utils.File(url, settings, retry=False)
        self.assertTrue(isinstance(file, file_utils.LocalFile))

    def testFactoryLocalFileNoProtocol(self):
        url = self.filepath
        settings = {}
        file = file_utils.File(url, settings, retry=False)
        self.assertTrue(isinstance(file, file_utils.LocalFile))

    def testFactoryFileInvalidProtocol(self):
        url = 'tcp://'+self.filepath
        settings = {}
        with self.assertRaises(file_utils.FileUtilsError):
            file = file_utils.File(url, settings, retry=False)

class TestLocalFile(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.filename = 'file0.txt'
        self.filepath = os.path.join(self.tempdir, self.filename)
        with open(self.filepath, 'w') as f:
            f.write(self.filename)
        self.md5 = '78dcf3b0d4ad2a2b283f7fba8c441faa'
        settings = {}
        self.file = file_utils.File(self.filepath, settings, retry=False)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def testCalculateMd5(self):
        self.assertEqual(self.file.calculate_md5(), self.md5)

    def testGetUrl(self):
        self.assertEqual(self.file.get_url(), 'file://'+self.filepath)

    def testGetPath(self):
        self.assertEqual(self.file.get_path(), self.filepath)

    def testGetFilename(self):
        self.assertEqual(self.file.get_filename(), self.filename)

    def testExists(self):
        self.assertTrue(self.file.exists())

    def testExistsNegative(self):
        file = file_utils.File('/no/file/here/friend', {})
        self.assertFalse(file.exists())

    def testIsDir(self):
        file = file_utils.File(self.tempdir, {})
        self.assertTrue(file.is_dir())

    def testIsDirNegative(self):
        self.assertFalse(self.file.is_dir())

    def testRead(self):
        self.assertEqual(self.file.read(), self.filename)

    def testWrite(self):
        newfile = file_utils.File(os.path.join(self.tempdir, 'newfile'), {})
        newtext = 'newtext'
        newfile.write(newtext)
        self.assertEqual(newfile.read(), newtext)

    def testDelete(self):
        self.file.delete()
        self.assertFalse(self.file.exists())

    def testDeleteWithPruneTo(self):
        subdir1 = 'one'
        subdir2 = 'two'
        filename = 'file.txt'
        filepath = os.path.join(self.tempdir, subdir1, subdir2, filename)
        os.mkdir(os.path.join(self.tempdir, subdir1))
        os.mkdir(os.path.join(self.tempdir, subdir1, subdir2))
        file = file_utils.File(filepath, {})
        file.write('hey')
        file.delete(pruneto=os.path.join(self.tempdir, subdir1))
        self.assertTrue(os.path.exists(
            os.path.join(self.tempdir, subdir1)))
        self.assertFalse(os.path.exists(
            os.path.join(self.tempdir, subdir1, subdir2)))

class TestGoogleStorageFile(unittest.TestCase):

    def setUp(self):
        self.settings = {'GCE_PROJECT': ''}
        self.file = file_utils.File(
            SAMPLE_GOOGLE_STORAGE_FILE, self.settings, retry=False)

    def testCalculateMd5(self):
        self.assertEqual(self.file.calculate_md5(), 'f16f91efe578419767b9dadaebcdc158')

    def testGetUrl(self):
        self.assertEqual(self.file.get_url(), SAMPLE_GOOGLE_STORAGE_FILE)

    def testGetPath(self):
        bucket_and_path = re.sub('^gs://', '', SAMPLE_GOOGLE_STORAGE_FILE)
        path = '/'+'/'.join(bucket_and_path.split('/')[1:])
        self.assertEqual(self.file.get_path(), path)

    def testGetFilename(self):
        self.assertEqual(self.file.get_filename(),
                         os.path.basename(SAMPLE_GOOGLE_STORAGE_FILE)
        )

    def testExists(self):
        self.assertTrue(self.file.exists())

    def testExistsNegative(self):
        file = file_utils.File(
            SAMPLE_GOOGLE_STORAGE_BUCKET+'/arent/any/files/here/friend',
            self.settings)
        self.assertFalse(file.exists())

    def testIsDir(self):
        file = file_utils.File(os.path.dirname(SAMPLE_GOOGLE_STORAGE_FILE)+'/',
                                self.settings)
        self.assertTrue(file.is_dir())

    def testIsDirNegative(self):
        self.assertFalse(self.file.is_dir())

    def testRead(self):
        text = self.file.read()
        self.assertTrue('Family_ID' in text[0:100])

    def testWrite(self):
        pass

    def testDelete(self):
        pass


if __name__ == '__main__':
    unittest.main()
