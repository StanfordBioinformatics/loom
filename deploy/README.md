# Deploying XPPF clusters using Elasticluster

Elasticluster is a tool that simplifies cluster deployment on cloud platforms. It uses Ansible behind the scenes to help accomplish this. We can use Elasticluster to quickly and easily bring up clusters running XPPF.

In general, we follow these instructions for setting up Elasticluster: http://googlegenomics.readthedocs.org/en/latest/use_cases/setup_gridengine_cluster_on_compute_engine/#install-elasticluster-on-your-workstation-laptop

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

Finally, you may need to add a firewall rule to your Google Cloud Project to allow connecting to instances from your machine: https://cloud.google.com/compute/docs/networking#firewalls

#### 4. Test your elasticluster installation:

```
elasticluster start -vvv mycluster
elasticluster list-nodes mycluster
elasticluster ssh mycluster
exit
```

#### 5. Make sure XPPF webserver is running and accessible from your machine:

```
curl <frontend-node-ip>:8000/api/steps
```

#### 6. Take down running cluster:

```
elasticluster stop mycluster
```

#### TODO:
- Once ansible 1.9.3 and a supporting version of elasticluster have been added to pip repository, make a requirements.txt.

#### Other thoughts:
- Elasticluster's export and import commands might be a better way of getting up and running. However, this only saves the step of editing .elasticluster/config using config_template. Would still need to install software, add roles, and get SSH keys and API keys.
- Could skip steps 1 and 2 by distributing a Docker container with Elasticluster/Ansible/roles already configured for XPPF. However, users would still have to do final cluster configuration and key management, and make config file visible to Docker container. Would require Docker on client machine. Typing "docker run -v /home/username/.elasticluster:/home/xppf/.elasticluster xppf/elasticluster start" is clunky (but could make a script for that).
