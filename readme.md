###이 문서는 간단한 BareOS 설치법과, 백업된 파일에서 특정 파일만을 restore 하는 방법을 다룸###

===BareOS install===
CentOS7.x 에서 진행

===설치 순서===
1. install.sh 실행
2. pgsql 설치
#yum install postgresql96*
#ln -s /usr/pgsql-9.6/bin/pg_config /usr/bin/pg_config
#service postgresql-9.6 initdb

3. python-bareos 설치 (아래 repo 추가)

/etc/yum.repos.d/bareos_contrib.repo 파일내용

[bareos_contrib]
name=Bareos project contributions (CentOS_7)
type=rpm-md
baseurl=http://download.bareos.org/bareos/contrib/CentOS_7/
gpgcheck=1
gpgkey=http://download.bareos.org/bareos/contrib/CentOS_7//repodata/repomd.xml.key
enabled=1

yum 으로 설치
#yum install python-bareos
#pip install sslpsk

※sslpsk 설치 실패날 경우
yum install python-devel libxslt-devel libffi-devel openssl-devel
yum install gcc gcc-c++

※sslpsk 가 설치안되는 python2.6에서의 해결법
/usr/lib/python2.6/site-packages/bareos/bsock/lowlevel.py 파일의 {} 를 수정해준다.
{} {} -> {0} {1}

4. 클라이언트 설치 (백업대상 서버들에 설치)
/etc/yum.repos.d/bareos.repo 파일 내용

[bareos_bareos-18.2]
name=bareos:bareos-18.2 (CentOS_6)
type=rpm-md
baseurl=http://download.bareos.org/bareos/release/18.2/CentOS_6/
gpgcheck=1
gpgkey=http://download.bareos.org/bareos/release/18.2/CentOS_6/repodata/repomd.xml.key
enabled=1

yum install bareos-filedaemon bareos-filedaemon-python-plugin

설정에 대한 예시는 공식문서 참고 할것

##########백업파일에서의 특정 파일들 복원 방법##########
-> Bareos 내부적으로 사용 가능한 API 가 구현되어 있음 (.bvfs API)
.bvfs API 를 사용하여 백업된 단일 파일에서 특정 부분만을 복원처리할 수 있음

예시)
데이터 백업디렉토리는 /local_backup 이며, 백업 대상 디렉토리는 /www 이다.
/www/kkari_net/test 라는 디렉토리가 있었다고 할 때, kkari_net 디렉토리만 복원하는 방법 예시
(업로드되어있는 bareos_restore.py 참조)

1. 복원을 원하는 서버의 job id를 알아야 함
-> master 서버 DB에 저장되어 있는 데이터에서 백업 날짜 / 대상서버 로 추출 가능하다
-> jobid = 205 라고 가정

2. 알아낸 job id 로 해당 복원에 필요한 job 들을 추출
.bvfs_get_jobids jobid=205 (결과값은 여러개 뜰 수도 있다.)
-> 결과: 205

3. .bvfs_update 명령어로 bvfs 캐시를 생성
.bvfs_update jobid=205

4. 원하는 백업 디렉토리를 찾는 과정 (/www/kkari_net 을 백업데이터에서 찾아야 함)
.bvfs_Isdirs jobid=205 path=/
->
1091    0       0       A A A A A A A A A A A A A A     .
1092    0       0       A A A A A A A A A A A A A A     ..
68      54617607        205     gJ C EHt D A A A DAA BAA Y Bdt6IF Bdt6IF Bdt6IF A A d   www/

4.1 www/ 가 보이므로 해당 디렉토리의 path로 진입 (68)
.bvfs_lsdirs jobid=205 path=/www/
->
68      54617607        205     gJ C EHt D A A A DAA BAA Y Bdt6IF Bdt6IF Bdt6IF A A d   .
1091    0       0       A A A A A A A A A A A A A A     ..
658     54617606        205     gJ jAAB EHt R H3 H4 A BAA BAA I Bdtx6T BdjHm/ BdsWBi A A d      kkari_net/

4.2 kkari_net 디렉토리의 dirid(658) 을 알아낸 뒤 복원테이블 생성(DB)
.bvfs_restore jobid=205 dirid=658 path=b2 + "랜덤으로몇개의숫자 아무거나입력"
-> .bvfs_restore jobid=205 dirid=658 path=b821459

4.3 마스터 DB에서 확인하면 b821459 테이블이 생긴 것을 확인할 수 있다.
-> 테이블 데이터에는 복원할 파일의 index와 fileid가 있다

5. 복원 명령어로 복원 진행
restore file=?b821459 client=localhost where=/ yes
-> /www/kkari_net 하위 데이터가 복원되었다.

6. 복원후 캐시 삭제
.bvfs_cleanup path=b821459 (DB테이블 삭제)
.bvfs_clear_cache yes
