# -*- coding: utf-8 -*-
"""
Created on Sat Jul  4 19:24:38 2020

@author: ε_ω
"""

from bs4 import BeautifulSoup
import requests
import json
import time
import datetime

"""
製品情報取得基底クラス
"""
class ProductGetterBase:
    
    STATUS_NONE = 0
    STATUS_GOOD = 1
    STATUS_BAD = 2
    
    """
    0: URL
    1: 商品名
    2: ステータス
    """
    productInfos = []
    
    def __init__(self):
        return
    
    
    """
    更新して差分を出力
    """
    def UpdateProduct(self, NewProduct):
        
        diffInfos = []
        for newInfo in NewProduct.productInfos:
        
            contains = False    
        
            for i in range(len(self.productInfos)):
                
                # prevと一致する商品URLを見つけてステータスの変化を検出する
                if newInfo[0] == self.productInfos[i][0]:
                    
                    # ステータスが違ったらdiffを残して更新
                    if newInfo[2] != self.productInfos[i][2]:
                        
                        self.productInfos[i] = newInfo
                        diffInfos.append(newInfo)
                    
                    contains = True
                    break;
                
            if not contains:
                
                self.productInfos.append(newInfo)
                diffInfos.append(newInfo)
            
        return diffInfos
    
    
    """
    ステータスなしのアイテムを出力
    """
    def OutputStatusNone(self):
        
        for x in self.productInfos:
            if x[2] == self.STATUS_NONE: print(x[1])


"""
ヨドバシ
"""
class YodobashiNotify(ProductGetterBase):

    keyword = '***'
    
    baseUrl = 'https://www.yodobashi.com'
    pageLeftUrl = 'https://www.yodobashi.com/p'
    pageRightUrl = '/?discontinued=true&count=48&ginput=' + keyword + '&sorttyp=NEW_ARRIVAL_RANKING&word=' + keyword
    
    headers = {'User-Agent': '***'}
    
    payload = {'Accept': '***',
    'Accept-Encoding': '***',
    'Accept-Language': '***',
    'Cache-Control': '***',
    'Connection': '***',
    'DNT': '***',
    'Host': 'www.yodobashi.com',
    'Sec-Fetch-Dest': '***',
    'Sec-Fetch-Mode': '***',
    'Sec-Fetch-Site': '***',
    'Sec-Fetch-User': '***',
    'Upgrade-Insecure-Requests': '***',}
    
    def __init__(self):
        
        super().__init__()
        self.GetProduct()
    
    
    """
    製品情報を取得
    """
    def GetProduct(self):
        
        self.productInfos = []
        for p in range(1, 6):
            
            url = self.pageLeftUrl + str(p) + self.pageRightUrl
        
            r =  requests.get(url, headers=self.headers, data=json.dumps(self.payload))
            masterSoup = BeautifulSoup(r.text, 'html.parser')
            r.close()
            
            productDivs = masterSoup.find_all('div', class_='srcResultItem_block pListBlock hznBox js_productBox js_smpClickable productListTile')

            for productDiv in productDivs:
                
                productUrl = self.GetProductUrl(productDiv)
                productName = self.GetProductName(productDiv)
                productStatus = self.GetProductStatus(productDiv)
                
                self.productInfos.append([productUrl, productName, productStatus])
    
    """
    URL
    """
    def GetProductUrl(self, soup):
        
        link = soup.find('a', class_='js_productListPostTag js-clicklog js-taglog-schRlt js_smpClickableFor cImg')
        
        return self.baseUrl + link.get('href')
    
    
    """
    商品名
    """
    def GetProductName(self, soup):
        
        nameArea = soup.find('div', class_='pName fs14').text
        
        pSplit = nameArea.split('<p>')
        spSplit = pSplit[-1].split('</p>')
        
        return spSplit[0]
    
    
    """
    ステータス
    """
    def GetProductStatus(self, soup):
        
        statusArea = soup.find('div', class_='pInfo').text
        
        goodText = ['在庫あり', 'ただいま予約受付中！', 'すぐ読めます', '在庫残少 ご注文はお早めに！', '発売日以降お届け']
        badText = ['予約受付を終了しました', '販売休止中です', '予定数の販売を終了しました', '販売を終了しました']
        
        goodStatusFlags = []
        for x in goodText: goodStatusFlags.append(x in statusArea)
        
        badStatusFlags = []
        for x in badText: badStatusFlags.append(x in statusArea)
        
        if (any(goodStatusFlags)):
            return self.STATUS_GOOD
        
        if (any(badStatusFlags)):
            return self.STATUS_BAD
        
        return self.STATUS_NONE


    """
    更新
    """
    def Update(self):
        
        return self.UpdateProduct(YodobashiNotify())
    
    
    """
    タイトル
    """
    def GetTitle(self):
        
        return 'Yodobashi'


"""
ビックカメラ
"""
class BicCameraNotify(ProductGetterBase):

    keyword = '***'
    pageLeftUrl = 'https://www.biccamera.com/bc/category/?q=' + keyword + '&sort=01&rowPerPage=100&p='
    
    headers = {'user-agent': '***'}
    
    payload = {
    ':authority': 'www.biccamera.com',
    ':method': 'GET',
    ':path': '/bc/category/?q=' + keyword + '&sort=01&rowPerPage=100',
    'scheme': 'https',
    'accept': '***',
    'accept-encoding': '***',
    'accept-language': '***',
    'cache-control': '***',
    'dnt': '***',
    'sec-fetch-dest': '***',
    'sec-fetch-mode': '***',
    'sec-fetch-site': '***',
    'sec-fetch-user': '***',
    'upgrade-insecure-requests': '***'}
    
    
    def __init__(self):
        
        super().__init__()
        self.GetProduct()
    
    
    """
    製品情報を取得
    """
    def GetProduct(self):
        
        self.productInfos = []
        for p in range(1, 3):
            
            url = self.pageLeftUrl + str(p)
        
            r =  requests.get(url, headers=self.headers)#, data=json.dumps(self.payload))
            r.encoding = r.apparent_encoding
            masterSoup = BeautifulSoup(r.text, 'html.parser')
            r.close()
            
            productDivs = masterSoup.find_all('li', attrs={'data-item': 'data-item'})
            
            for productDiv in productDivs:
                
                productUrl = self.GetProductUrl(productDiv)
                productName = self.GetProductName(productDiv)
                productStatus = self.GetProductStatus(productDiv)
                
                self.productInfos.append([productUrl, productName, productStatus])
    
    """
    URL
    """
    def GetProductUrl(self, soup):
        
        link = soup.find('a', class_='cssopa')
        
        return link.get('href')
    
    
    """
    商品名
    """
    def GetProductName(self, soup):
        
        return soup.get('data-item-name')
    
    
    """
    ステータス
    """
    def GetProductStatus(self, soup):
        
        statusArea = soup.text
        
        goodText = ['在庫あり', 'ただいま予約受付中！', 'すぐ読めます', '在庫残少 ご注文はお早めに！', '発売日以降お届け']
        badText = ['予約受付を終了しました', '販売休止中です', '予定数の販売を終了しました', '販売を終了しました']
        
        goodStatusFlags = []
        for x in goodText: goodStatusFlags.append(x in statusArea)
        
        badStatusFlags = []
        for x in badText: badStatusFlags.append(x in statusArea)
        
        if (any(goodStatusFlags)):
            return self.STATUS_GOOD
        
        if (any(badStatusFlags)):
            return self.STATUS_BAD
        
        return self.STATUS_NONE


    """
    更新
    """
    def Update(self):
        
        return self.UpdateProduct(BicCameraNotify())
    
    
    """
    タイトル
    """
    def GetTitle(self):
        
        return 'BicCamera'
    

def PostLINENotify(title, diffInfos):
    
    str = ''
    for info in diffInfos:
        
        if info[2] == ProductGetterBase.STATUS_GOOD:
            
            str += '★' + info[1] + '\n' + info[0] + '\n'
            
    if len(str) > 0:
        
        token = "***"
        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": "Bearer " + token}
        payload = {"message": '\n[' + title + '入荷情報]\n' + str}
        requests.post(url, headers=headers, data=payload)


notifies = [YodobashiNotify(), BicCameraNotify()]

try:
    
    while True:  
    
        time.sleep(300)
        
        print(datetime.datetime.today())
        
        
        for notify in notifies:
            
            diffInfos = notify.Update()
            print(notify.GetTitle())
            print(diffInfos)
            PostLINENotify(notify.GetTitle(), diffInfos)
        
finally:
    
    token = "***"
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": "Bearer " + token}
    payload = {"message": 'end'}
    requests.post(url, headers=headers, data=payload)  