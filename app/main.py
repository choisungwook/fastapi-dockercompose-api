import secrets

from fastapi import Depends, FastAPI, HTTPException, status, Form, File
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import subprocess
import logging
import sys
import docker

logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)

app = FastAPI()
security = HTTPBasic()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    '''Http basic auth 검사'''

    correct_username = secrets.compare_digest(credentials.username, "user")
    correct_password = secrets.compare_digest(credentials.password, "password")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

class DockerComposeHelper:
    '''docker-comopse 명령실행을 위한 helper'''

    def __init__(self, docker_compose_binary, repo_name):
        '''
        :params

        docker_compose_binary: docker_compose 파일 데이터
        dirroot: docker-compose를 저장할 디렉터리 루트 경로        
        dirname: docker-compose를 저장할 디렉터리 이름
        outputdir: docker-compose를 저장할 디렉터리 전체 경로
        filepath: docker-compose 파일 전체 경로        
        '''

        self.docker_compose_binary = docker_compose_binary
        self.dirroot = os.path.join("/app/data")
        self.dirname = self.CreateDockercomposeDirname(repo_name)        
        self.outputdir = os.path.join(self.dirroot, self.dirname)
        self.filepath = os.path.join(self.outputdir, 'docker-compose.yaml')

    def StringTofile(self):
        '''docker-compose 문자열을 파일로 변환'''

        os.makedirs(self.outputdir, exist_ok=True)

        with open(self.filepath, 'wb') as f:
            f.write(self.docker_compose_binary)

    def DeleteDockercomposefile(self):
        '''docker-compose파일과 디렉터리 삭제'''

        shutil.rmtree(self.outputdir)
    
    def RunDockercompose(self):
        '''docker-compose 실행'''
        
        response = {
            'status': '',
            'error_msg': ''
        }

        logger.debug("file create start")
        self.StringTofile()
        logger.debug("file create done")
        
        try:
            logger.debug("run docker-compose up -d start")
            command = ['docker-compose', '-f', f'{self.filepath}', 'up', '-d', '--force-recreate']
            dockercompose_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = dockercompose_process.communicate()
            logger.debug("run docker-compose up -d done")

            if dockercompose_process.returncode != 0:
                response['status'] = False
                response['error_msg'] = stderr
            else: 
                response['status'] = True
        except OSError as e:
            logger.error(f"docker-compose up OSError exception: {e}")
            response['status'] = False
            response['error_msg'] = str(e)
        except Exception as e:
            logger.error(f"docker-compose up exception: {e}")
            response['status'] = False
            response['error_msg'] = str(e)
        finally:
            return response

    def DeleteDockercompose(self):
        '''docker-compose 삭제'''
        
        response = {
            'status': '',
            'error_msg': ''
        }
        
        try:
            logger.debug("run docker-compose down -d start")
            command = ['docker-compose', '-f', f'{self.filepath}', 'down']
            dockercompose_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = dockercompose_process.communicate()
            logger.debug("run docker-compose down -d done")

            if dockercompose_process.returncode != 0:
                response['status'] = False
                response['error_msg'] = stderr
            else: 
                response['status'] = True
        except OSError as e:
            logger.error(f"docker-compose down OSError exception: {e}")
            response['status'] = False
            response['error_msg'] = str(e)
        except Exception as e:
            logger.error(f"docker-compose down exception: {e}")
            response['status'] = False
            response['error_msg'] = str(e)
        finally:
            self.DeleteDockercomposefile()
            return response

    def CreateDockercomposeDirname(self, repo_name):
        '''
        docker-compose를 저장할 디렉터리 이름 생성

        :return
          "/"를 "_"로 교체
        '''

        return repo_name.replace("/", "_")

def DeleteDockerImage(dockerimage):
    '''도커 이미지 삭제'''
    
    client = docker.from_env()
    client.images.remove(dockerimage)

@app.post("/create")
def RunDockerCompose(docker_compose: bytes = File(...),
                    repo_name: str = Form(...),
                    username: str = Depends(get_current_username)):
    '''docker compose 생성(있으면 업데이트)'''

    dockercompose_helper = DockerComposeHelper(
        docker_compose_binary = docker_compose, 
        repo_name = repo_name
    )
    dockercompose_response = dockercompose_helper.RunDockercompose()

    if dockercompose_response['status']:
        return "success"
    
    else:
        return dockercompose_response['error_msg']

@app.post("/delete")
def DeleteCompose(docker_compose: bytes = File(...),
                    repo_name: str = Form(...),
                    username: str = Depends(get_current_username)):
    '''docker compose 삭제'''

    dockercompose_helper = DockerComposeHelper(
        docker_compose_binary = docker_compose, 
        repo_name = repo_name
    )
    dockercompose_response = dockercompose_helper.DeleteDockercompose()

    if dockercompose_response['status']:
        return "success"
    
    else:
        return dockercompose_response['error_msg']
    