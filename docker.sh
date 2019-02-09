apt update
apt install docker.io docker -y
docker build -t enum_domain .
PWD=$(pwd)
docker run  -idt  --name enum_domain --restart=always -v $PWD:/root/ enum_domain
