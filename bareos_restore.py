#!/usr/bin/python
# -*- coding: utf-8 -*-

#받는파라미터 : 도메인,서버ip ,백업시점날짜, (ftp id)
#날짜파라미터 양식 ex) 2019-10-28

import pymysql
import psycopg2
import bareos.bsock
from random import randint

#bareos-dir.d/director/bareos-dir.conf password
password = bareos.bsock.Password('[PASSWORD]')
directorconsole = bareos.bsock.DirectorConsoleJson(address='[HOST]',name='[LOCALHOST]', port=9101,password=password)

#db연결 부분
conn_string = "host='[HOST]' dbname='bareos' user='bareos' password='[PASSWORD]'"
conn = psycopg2.connect(conn_string)

#테스트로 넣은 값들
client = '[LOCALHOST]'
date = '2020-11-09'
data_dir = '/www/kkari_net'

#DB쿼리 결과를 반환
def Dbquery(conn,sql) :
        curs = conn.cursor()
        curs.execute(sql)
        rows =curs.fetchone()
        conn.close()
        return rows

#백업을 복원할 Jobid 들을 찾아서 반환 (Jobid는 여러개)
def Getjobid(client,date) :
        query = "SELECT JobId FROM Job WHERE ClientId=(SELECT ClientId FROM Client WHERE NAME='%s') AND name='%s_daily' AND (JobStatus='T' OR JobStatus='W') AND type='B' AND EndTime::text LIKE '%%%s%%'" %(client,client,date)
        result = Dbquery(conn,query)
        #tuple
        jobid = result[0]
        api_string = ".bvfs_get_jobids jobid=%s" %(jobid)
        joblist = directorconsole.call('%s' %api_string)
        jobs = []
        for num in joblist.values() :
                for value in num :
                        jobs.append(value.values()[0])
                jobid = str(jobid) + ',' + ','.join(jobs)

        return jobid

#고객 백업파일 디렉토리id를 찾아서 반환
def FindBackup(jobid,data_dir) :
        data_dir = data_dir  + "/"
        api_string = ".bvfs_lsdirs jobid=%s path=%s" %(jobid,data_dir)
        result = directorconsole.call(api_string)
        for list in result.values() :
                for path in list :
                        if '.' == path['fullpath'] :
                                pathid = path['pathid']
        return pathid

#복원 DB테이블 생성후 테이블명 반환
def CreateDBtable(jobid,dirid) :
        randompath = str(randint(0,999999))
        tablepath = "b2" + randompath
        api_string = ".bvfs_restore jobid=%s dirid=%s path=%s" %(jobid,dirid,tablepath)
        directorconsole.call(api_string)
        return tablepath

#복원 진행
def RestoreBackup(tablepath,client) :
        api_string = "restore file=?%s client=%s where=/ yes" %(tablepath,client)
        directorconsole.call(api_string)

#복원후 DB테이블 삭제, 캐시 clear
def DeleteTable(tablepath) :
        api_string = ".bvfs_cleanup path=%s" %tablepath
        directorconsole.call(api_string)
        directorconsole.disconnect()

def main() :
        jobid = Getjobid(client,date)
        pathid = FindBackup(jobid,data_dir)
        RestoreBackup(tablepath,client)
        DeleteTable(tablepath)

if __name__ == "__main__":
        try:
                main()
        except Exception as e:
                print(e)
