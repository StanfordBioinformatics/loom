# Deploying XPPF clusters using elasticluster

In general, we follow these instructions for setting up elasticluster: http://googlegenomics.readthedocs.org/en/latest/use_cases/setup_gridengine_cluster_on_compute_engine/#install-elasticluster-on-your-workstation-laptop

However, there are several important differences:
- we use Slurm instead of Grid Engine
- we add Ansible roles for Docker and XPPF

#### 1. Set up ansible and elasticluster in a virtualenv:

```
virtualenv elasticluster
cd elasticluster
source bin/activate
git clone https://github.com/ansible/ansible.git
cd ansible
git checkout v1.9.3-0.2.rc2
git submodule update --init --recursive
python setup.py install
cd ..
git clone https://github.com/gc3-uzh-ch/elasticluster.git
cd elasticluster
python setup.py install
```

#### 2. Add Docker and XPPF roles:

```
cd elasticluster/providers/ansible-playbooks/roles
ansible-galaxy install -p . angstwad.docker_ubuntu
cp <path-to-xppf-repo>/xppf/deploy/docker.yml <path-to-xppf-repo>/xppf/deploy/xppf.yml .
```

Edit elasticluster/elasticluster/providers/ansible-playbooks/site.yml and add these two lines at the bottom:

```
- include: roles/docker.yml
- include: roles/xppf.yml
```

#### 3. Edit ~/.elasticluster/config, using xppf/deploy/config_template as a template.

If you haven't used gcloud ssh with your Google Cloud Project before, you'll need to generate SSH keys as outlined here: http://googlegenomics.readthedocs.org/en/latest/use_cases/setup_gridengine_cluster_on_compute_engine/#generating-your-ssh-keypair

Also, you can find your project ID, client ID, and client secret by following these instructions: http://googlegenomics.readthedocs.org/en/latest/use_cases/setup_gridengine_cluster_on_compute_engine/#obtaining-your-client-id-and-client-secret

#### 4. Test your elasticluster installation:

```
elasticluster start -vvv mycluster
elasticluster list-nodes mycluster
elasticluster ssh mycluster
exit
```

#### 5. Make sure XPPF webserver is running:

```
curl <frontend-node-ip>:8000/api/steps
```

#### 6. Take down running cluster:

```
elasticluster stop mycluster
```

#### TODO:
- Once ansible 1.9.3 and a supporting version of elasticluster have been added to pip repository, make a requirements.txt.
