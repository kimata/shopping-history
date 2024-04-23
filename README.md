# shopping-history

shopping-history は，下記のショップの購入履歴を収集し，
サムネイル付きの Excel 形式で出力するソフトウェアです．

- Yahoo!ショッピング
- アマゾン
- メルカリ
- モノタロウ
- ヨドバシ.com

## 動作環境

基本的には，Python と Selenium が動作する環境であれば動作します．
下記の環境での動作を確認しています．

- Linux (Ubuntu 22.04)
- Windows 11

## 設定

同封されている `config.example.yaml` を `config.yaml` に名前変更して，下記の部分を書き換えます．

```yaml:config.yaml
  amazon:
    user: Amazon.co.jp のユーザ名
    pass: Amazon.co.jp のパスワード
    
  yahoo:
    user: Yahoo! のユーザ名
    mail: Yahoo! に登録したメールアドレス

  yodobashi:
    user: ヨドバシ.com のユーザ名
    pass: ヨドバシ.com のパスワード
    
  monotaro:
    user: モノタロウのユーザ名
    pass: モノタロウに登録したメールアドレス
    
  mercari:
    user: メルカリのユーザ名
    pass: メルカリのパスワード
```
## Linux での動かし方

### 必要なパッケージのインストール

実行に際して `docker-compose` を使用しますので，インストールします．
Ubuntu の場合，以下のようにします．

```
sudo apt install docker-compose
```
### 実行

以下のようにします．`build` は一回だけ実行すればOKです．

```
docker-compose build
docker-compose run --rm shopping-history
```

取引履歴の数が沢山ある場合，1時間以上がかかりますので，放置しておくのがオススメです．

なお，何らかの事情で中断した場合，再度実行することで，途中から再開できます．
コマンドを実行した後に注文履歴が増えた場合も，再度実行することで前回以降のデータからデータ収集を再開できます．

### Docker を使いたくない場合

[Poetry](https://python-poetry.org/) と Google Chrome がインストールされた環境であれば，
下記のようにして Docker を使わずに実行することもできます．

```
poetry install
poetry run app/crawler.py
```

## ライセンス

Apache License Version 2.0 を適用します．
