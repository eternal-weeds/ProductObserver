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
    # 商品の在庫情報
    STATUS_NONE = 0 # 在庫情報取得失敗
    STATUS_GOOD = 1 # 在庫あり
    STATUS_BAD = 2 # 在庫なし
    
    """
    商品情報を保存する配列(2次元)
    
     1次元目: 商品ごとの情報
    
     2次元目: 商品の詳細情報
      0: URL
      1: 商品名
      2: ステータス
    """
    productInfos = []
    
    
    """
    コンストラクタ
    """
    def __init__(self):
        return
    
    
    """
    更新して差分を出力
    
     @ NewProduct: 商品情報
    """
    def UpdateProduct(self, NewProduct):
        # selfの商品情報と引数の商品情報の差分(入荷情報)保存用配列
        diffInfos = []
        
        # 2つの商品情報を全比較して（在庫なし→在庫あり）に変化しているものを検出
        for newInfo in NewProduct.productInfos:
            # 新しい商品情報があるか
            contains = False    
        
            for i in range(len(self.productInfos)):
                # prevと一致する商品URLを見つけてステータスの変化を検出する
                if newInfo[0] == self.productInfos[i][0]:
                    # ステータスが違ったらdiffを残して更新
                    if newInfo[2] != self.productInfos[i][2]:
                        self.productInfos[i] = newInfo
                        diffInfos.append(newInfo)
                    
                    # 新しい商品情報が見つかった
                    contains = True
                    break;
                
            # 新しい商品情報だったら商品情報と入荷情報の両方に追加
            if not contains:
                self.productInfos.append(newInfo)
                diffInfos.append(newInfo)
            
        return diffInfos
    
    
    """
    商品情報取得失敗のアイテムを出力(エラー確認用)
    """
    def OutputStatusNone(self):
        for x in self.productInfos:
            if x[2] == self.STATUS_NONE: print(x[1])


"""
ヨドバシ
"""
class YodobashiNotify(ProductGetterBase):
    # 商品URL生成用のベースURL
    baseUrl = 'https://www.yodobashi.com'
    
    # 検索URL(ページ番号は動的に加える)
    keyword = '***'
    pageLeftUrl = 'https://www.yodobashi.com/p'
    pageRightUrl = '/?discontinued=true&count=48&ginput=' + keyword + '&sorttyp=NEW_ARRIVAL_RANKING&word=' + keyword
    
    # ヘッダー情報(chromeとかでRequestHeaderから取ってきてコピペ)
    headers = {'User-Agent': '***'}
    
    # ペイロード情報(chromeとかでRequestHeaderから取ってきてコピペ)
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
    
    
    """
    コンストラクタ
    """
    def __init__(self):
        super().__init__()
        # 在庫情報を取得
        self.GetProduct()
    
    
    """
    製品情報を取得
    """
    def GetProduct(self):
        # 商品情報を構築する配列
        self.productInfos = []
        
        # キーワード検索した結果の1～2ページ目から商品情報を取得
        for p in range(1, 6):
            url = self.pageLeftUrl + str(p) + self.pageRightUrl
        
            # 通販サイトへGETリクエスト
            r =  requests.get(url, headers=self.headers, data=json.dumps(self.payload))
            masterSoup = BeautifulSoup(r.text, 'html.parser')
            r.close()
            
            # 通販サイトの検索ページは1ページに複数の商品情報があるためそれを1個ずつ切り分ける
            productDivs = masterSoup.find_all('div', class_='srcResultItem_block pListBlock hznBox js_productBox js_smpClickable productListTile')

            # 各商品情報のhtmlテキストからURL、商品名、在庫状況を抽出して保存
            for productDiv in productDivs:
                productUrl = self.GetProductUrl(productDiv)
                productName = self.GetProductName(productDiv)
                productStatus = self.GetProductStatus(productDiv)
                
                self.productInfos.append([productUrl, productName, productStatus])
    
    """
    商品URL
    
    　@ soup: 商品URLを含む通販サイトのソースコードの一部
    """
    def GetProductUrl(self, soup):
        link = soup.find('a', class_='js_productListPostTag js-clicklog js-taglog-schRlt js_smpClickableFor cImg')
        
        return self.baseUrl + link.get('href')
    
    
    """
    商品名
    
     @ soup: 商品名を含む通販サイトのソースコードの一部
    """
    def GetProductName(self, soup):
        nameArea = soup.find('div', class_='pName fs14').text
        
        pSplit = nameArea.split('<p>')
        spSplit = pSplit[-1].split('</p>')
        
        return spSplit[0]
    
    
    """
    在庫情報取得
    
     通販サイトの在庫情報を抽出してプログラムで管理しやすい値に変換
     
     @ soup: 在庫情報を含む通販サイトのソースコードの一部
    """
    def GetProductStatus(self, soup):
        statusArea = soup.find('div', class_='pInfo').text
        
        # 通販サイト固有の在庫状況を表すテキスト(goodが在庫あり、badが在庫なし)
        goodText = ['在庫あり', 'ただいま予約受付中！', 'すぐ読めます', '在庫残少 ご注文はお早めに！', '発売日以降お届け']
        badText = ['予約受付を終了しました', '販売休止中です', '予定数の販売を終了しました', '販売を終了しました']
        
         # それぞれのgoodTextが含まれているかをテキストから検索
        goodStatusFlags = []
        for x in goodText: goodStatusFlags.append(x in statusArea)
        
        # それぞれのbadTextが含まれているかをテキストから検索
        badStatusFlags = []
        for x in badText: badStatusFlags.append(x in statusArea)
        
        # いずれかのgoodTextが見つかったら在庫あり
        #（万が一、在庫ありとなしが混在した場合は、入荷の見逃しを防ぐために在庫ありを優先する）
        if (any(goodStatusFlags)):
            return self.STATUS_GOOD
        
        # いずれかのbadTextが見つかったら在庫なし
        if (any(badStatusFlags)):
            return self.STATUS_BAD
        
        # 在庫情報検出失敗
        return self.STATUS_NONE


    """
    更新(TODO: 商品入荷情報の抽出に直す)
    
     最新の商品情報を取得して前回の商品情報(self)との差分による商品入荷情報を抽出
    """
    def Update(self):
        return self.UpdateProduct(YodobashiNotify())
    
    
    """
    通販サイトのタイトル
    """
    def GetTitle(self):
        return 'Yodobashi'


"""
ビックカメラ
"""
class BicCameraNotify(ProductGetterBase):
    # 検索URL(ページ番号は動的に加える)
    keyword = '***'
    pageLeftUrl = 'https://www.biccamera.com/bc/category/?q=' + keyword + '&sort=01&rowPerPage=100&p='
    
    # ヘッダー情報(chromeとかでRequestHeaderから取ってきてコピペ)
    headers = {'user-agent': '***'}
    
    # ペイロード情報(chromeとかでRequestHeaderから取ってきてコピペ)
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

    
    """
    コンストラクタ
    """
    def __init__(self):
        super().__init__()
        
        # 在庫情報を取得
        self.GetProduct()
    
    
    """
    製品情報を取得
    """
    def GetProduct(self):
        # 商品情報を構築する配列
        self.productInfos = []
        
        # キーワード検索した結果の1～2ページ目から商品情報を取得
        for p in range(1, 3):
            url = self.pageLeftUrl + str(p)
        
            # 通販サイトへGETリクエスト
            r =  requests.get(url, headers=self.headers)#, data=json.dumps(self.payload))
            r.encoding = r.apparent_encoding
            masterSoup = BeautifulSoup(r.text, 'html.parser')
            r.close()
            
            # 通販サイトの検索ページは1ページに複数の商品情報があるためそれを1個ずつ切り分ける
            productDivs = masterSoup.find_all('li', attrs={'data-item': 'data-item'})
            
            # 各商品情報のhtmlテキストからURL、商品名、在庫状況を抽出して保存
            for productDiv in productDivs:
                productUrl = self.GetProductUrl(productDiv)
                productName = self.GetProductName(productDiv)
                productStatus = self.GetProductStatus(productDiv)
                
                self.productInfos.append([productUrl, productName, productStatus])
    
    """
    商品URL
    
    　@ soup: 商品URLを含む通販サイトのソースコードの一部
    """
    def GetProductUrl(self, soup):
        link = soup.find('a', class_='cssopa')
        return link.get('href')
    
    
    """
    商品名
    
     @ soup: 商品名を含む通販サイトのソースコードの一部
    """
    def GetProductName(self, soup):
        return soup.get('data-item-name')
    
    
    """
    在庫情報取得
    
     通販サイトの在庫情報を抽出してプログラムで管理しやすい値に変換
     
     @ soup: 在庫情報を含む通販サイトのソースコードの一部
    """
    def GetProductStatus(self, soup):
        statusArea = soup.text
        
        # 通販サイト固有の在庫状況を表すテキスト(goodが在庫あり、badが在庫なし)
        goodText = ['在庫あり', 'ただいま予約受付中！', 'すぐ読めます', '在庫残少 ご注文はお早めに！', '発売日以降お届け']
        badText = ['予約受付を終了しました', '販売休止中です', '予定数の販売を終了しました', '販売を終了しました']
        
        # それぞれのgoodTextが含まれているかをテキストから検索
        goodStatusFlags = []
        for x in goodText: goodStatusFlags.append(x in statusArea)
        
        # それぞれのbadTextが含まれているかをテキストから検索
        badStatusFlags = []
        for x in badText: badStatusFlags.append(x in statusArea)
        
        # いずれかのgoodTextが見つかったら在庫あり
        #（万が一、在庫ありとなしが混在した場合は、入荷の見逃しを防ぐために在庫ありを優先する）
        if (any(goodStatusFlags)):
            return self.STATUS_GOOD
        
        # いずれかのbadTextが見つかったら在庫なし
        if (any(badStatusFlags)):
            return self.STATUS_BAD
        
        # 在庫情報検出失敗
        return self.STATUS_NONE


    """
    更新(TODO: 商品入荷情報の抽出に直す)
    
     最新の商品情報を取得して前回の商品情報(self)との差分による商品入荷情報を抽出
    """
    def Update(self):
        return self.UpdateProduct(BicCameraNotify())
    
    
    """
    通販サイトのタイトル
    """
    def GetTitle(self):
        return 'BicCamera'
    
"""
商品情報をLINEへ通知する
@title: 通販サイトタイトル
@diffInfos: 前回の商品情報と今回の商品情報の差分による商品入荷情報
"""
def PostLINENotify(title, diffInfos):
    # LINEに送るメッセージのバッファー
    str = ''
    
    # 商品入荷情報をすべてメッセージバッファーに書き込む
    for info in diffInfos:
        if info[2] == ProductGetterBase.STATUS_GOOD:
            str += '★' + info[1] + '\n' + info[0] + '\n'
            
    # 商品入荷情報があるときだけ通知する
    if len(str) > 0:
        token = "***"
        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": "Bearer " + token}
        payload = {"message": '\n[' + title + '入荷情報]\n' + str}
        requests.post(url, headers=headers, data=payload)


# 通販サイトごとのWebクローラーインスタンスを作成
notifies = [YodobashiNotify(), BicCameraNotify()]

# 更新頻度(秒)
UpdateTime = 300

# 終了時に通知を送る
try:
    # 無限ループで一定時間間隔でWebクローラーを作動させる
    while True:  
        time.sleep(UpdateTime)
        print(datetime.datetime.today())
        
        # 通販サイトごとに商品情報を更新して差分を抽出してLineに通知する
        for notify in notifies:
            diffInfos = notify.Update()
            print(notify.GetTitle())
            print(diffInfos)
            PostLINENotify(notify.GetTitle(), diffInfos)
   
finally:
    # 終了時のLINE通知
    token = "***"
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": "Bearer " + token}
    payload = {"message": 'end'}
    requests.post(url, headers=headers, data=payload)  
        