#!/usr/bin/env python
# coding: utf-8

# In[1]:


import time
import datetime as dt
from pykrx import stock
import pandas as pd

import requests
from bs4 import BeautifulSoup
from tabulate import tabulate

today = dt.datetime.now()

stock_code_KOSPI = stock.get_market_ticker_list(date = "%d%02d%02d"%(
    today.year, today.month, today.day), market = "KOSPI")

stock_value = stock.get_market_fundamental_by_ticker(date = "20220517", market = "ALL")




# 주식 코드를 입력하면 주식명을 알려주는 함수
def find_stock(code_list): #code_list는 주식코드 리스트
    target_list = []
    
    df = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header = 0)[0]
    #전체 주식정보 불러오기
    df_name_code = df[['회사명', '종목코드']]
    #필요한 열만 추출
    
    for i in code_list:
        stock_name = str(df_name_code[df_name_code["종목코드"] == int(i)].회사명).split()[1]
        target_list.append(stock_name)
        
    return target_list



#PER > 0, 0.2 < PBR < 1 를 만족하는 종목코드만 리스트로 반환하는 함수
def find_value_list(df): #df는 stock_value
    target_code_list = []
    target_list = []
    a = df
    
    #a = df[df["PER"] < 10] # PER 10 이상 제거
    a = a[a["PER"] > 0] #PER 0 이하 제거
    a = a[a["PBR"] < 1] #PBR 1 이상 제거
    a = a[a["PBR"] > 0.2] #PBR 0.2 이하 제거(순자산과 주가 모두 낮을 가능성)
    a = a.sort_values(by = ["BPS"], ascending = False) #BPS 높은 순서로 정렬
    
    df = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header = 0)[0]
    #전체 주식정보 불러오기
    df_name_code = df[['회사명', '종목코드']]
    #필요한 열만 추출
    
    for target in a.index:
        target_list.append(str(df_name_code[df_name_code['종목코드']== int(target)].회사명).split()[1])
        target_code_list.append(target)
        
    return target_code_list



def fs_data(code): #크롤링 재무정보 저장
    url = "http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701&gicode="+code
    res = requests.get(url)
    df = pd.read_html(res.text)
    return df



def A_code(code_list): #(A+코드)로 수정, 파라미터 값은 코드 리스트
    code = ['A%s'%(i) for i in code_list]
    return code



stock_list = find_value_list(stock_value)


final_list = []
#최근 3분기 동안 매출이 상승 추세인지 확인
for i in range(len(stock_list)):
    df = fs_data(A_code(stock_list)[i])[1]
    
    take0 = df.iloc[0][1]
    take1 = df.iloc[0][2]
    take2 = df.iloc[0][3]
    try:
        if take0 < take1:
            if take1 < take2:
                final_list.append(stock_list[i])
            else:
                pass
        else:
            pass
    except:
        pass



GPA_list = []
#GP/A 구하기
for i in range(len(final_list)):
    
    df = fs_data(A_code(final_list)[i])[1]
    #분기별 재무정보
    total_profit= df.iloc[:,4].iloc[2]

    A = fs_data(A_code(final_list)[i])[3]
    Asset = A.iloc[:,4].iloc[0]

    GPA = total_profit / Asset
    GPA_list.append(GPA)



PBR_list = [stock_value.loc[i].PBR for i in final_list]
PER_list = [stock_value.loc[i].PER for i in final_list]

final_df = pd.DataFrame({'stock_code' : final_list, 'GP/A' :GPA_list, 'PBR' :PBR_list,
                        'PER' : PER_list})


target_list = [i for i in final_df.stock_code]
final_df.index = find_stock(target_list)



final_df.to_excel("2021-09-17.xlsx", engine = 'openpyxl')

