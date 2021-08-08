# 프로젝트 개요
* fastapi를 이용한 docker-compose API 애플리케이션 개발

# docker build
```sh
docker build -t <your-server>/<imagename>:<tag>
```

# docker push
```sh
docker push <your-server>/<imagename>:<tag>
```

# docker run
```sh
# 불륨 생성
docker volume create fastapi_dockerapi

# run
docker run --name=dockerapi \
-p 10090:80 \
--restart always \
--memory="256m" --cpu-shares=256 \
-v /var/run/docker.sock:/var/run/docker.sock \
-v fastapi_dockerapi:/app/data \
<your-server>/<imagename>:<tag>
```

# test docker-compose.yaml
## 파일 생성
```yaml
version: '3'
services:
  web:
    image: nginx:latest
    ports:
      - "30001:8080"
    expose:
      - "8080"
    networks:
      - our_net

networks:
  our_net:
    driver: bridge
```

## curl 테스트
```sh
# 생성
curl -X POST -u user:password -F 'docker_compose=@docker-compose.yaml' -F 'repo_name="test-a"' <your-serverip>:<docker port>/create

# 삭제
curl -X POST -u user:password -F 'docker_compose=@docker-compose.yaml' -F 'repo_name="test-a"' <your-serverip>:<docker port>/delete
```
