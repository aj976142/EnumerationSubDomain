apt update
apt install docker-ce -y
docker build -t enum_domain .
PWD=$(pwd)
docker run -d --name enum_domain --restart=always -v $PWD:/root/ enum_domain sh /root/start.sh
