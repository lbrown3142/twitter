import os
import paramiko
from scp import SCPClient


k = paramiko.RSAKey.from_private_key_file("Twitter_Explorer_Key.pem")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='52.31.43.191', username="ubuntu", pkey=k)

# SCPCLient takes a paramiko transport as its only argument
scp = SCPClient(ssh.get_transport())

files = [

]

for file in files:
    scp.put(file, os.path.join('TwitterExplorer/TwitterExplorer/TwitterExplorer', file))

scp.close()


ssh.close()
