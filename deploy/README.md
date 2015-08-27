# Deploying xppf clusters using elasticluster

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
cd ../share/elasticluster/providers/ansible-playbooks/roles
ansible-galaxy install -p . angstwad.docker_ubuntu
```

add docker.yml
add xppf.yml

edit share/elasticluster/providers/ansible-playbooks/site.yml to add the above two roles

edit ~/.elasticluster/config

elasticluster start mycluster
elasticluster list-nodes mycluster

curl <frontend-node-ip>:8000/api/steps

TODO: make requirements.txt (elasticluster 1.9.3 not in pip repository yet)
