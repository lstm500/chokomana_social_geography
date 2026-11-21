# ちょこまな｜しゃかい・ちり

日本地図の白地図に、出題された都道府県ピースをはめてから、名前を四択で答えます。PCではドラッグ、スマートフォンではドラッグまたは「ピース → 地図」の順にタップできます。ピースと地図は同じ縮尺で重なります。地方別7コースと全国47問があり、名前にはふりがなが付きます。

位置と名前の初回正誤をそれぞれ記録します。メダルは、ヒントなしで位置と名前をともに初回正解した数で判定します。全国コースでの地方拡大はヒント扱いです。

## 配置するファイル

地理用のGitHubリポジトリのルートに `app.py`、`README.md`、`requirements.txt` を置きます。画面・地図・学習ログの処理は `app.py` に入っています。SQLは同じフォルダーに同梱しています。

| 場所 | ファイル |
|---|---|
| 地理用のGitHubリポジトリ | `app.py`、`README.md`、`requirements.txt` |
| 既存のちょこまなと同じSupabase | `001_geography.sql` |
| 既存の集約アプリのGitHubリポジトリ | ZIP内の別フォルダーにある `hub/app.py`。添付された集約アプリの版を基にした更新済みファイル |

1. SupabaseのSQL Editorで、共通テーブルがあるプロジェクトにマイグレーションを適用します。
2. 地理アプリのリポジトリをStreamlit Community Cloudで公開し、Secretsに `SUPABASE_URL`、`SUPABASE_SERVICE_ROLE_KEY` または `SUPABASE_SECRET_KEY`、`CHOKOMANA_HOME_URL` を設定します。サービスキーはサーバーのSecretsに置きます。
3. 集約アプリを更新し、そのSecretsに `GEOGRAPHY_APP_URL` として地理アプリのHTTPS URLを設定します。
4. 地理アプリを一度開くと教材カタログを登録します。ホームで「しゃかい・ちり」を開き、地方別の問題を完了して「今日の成果」に「地」メダルが表示されることを確認します。地方別は「きょう やること」の候補に入り、全国47問は自由学習で開けます。当日の既存課題が確定している場合、新規選定は翌日からです。

ローカルでは `geography/` で `pip install -r requirements.txt` と `streamlit run app.py` を実行します。Supabase未設定でも遊べます。コース選択画面から端末内ログをJSONで保存できます。

## 学習記録

ホームの使い切り起動チケットで学習者と課題を引き継ぎます。Supabaseに保存した記録は、共通の `chokomana_learning_events` と `chokomana_stamps` から取得できます。`source_app = 'geography'` で絞り込んでください。

| 共通イベント | 内容 |
|---|---|
| `session_started` / `session_ended` | コース、課題ID、予定・回答数、終了状態 |
| `item_presented` / `response_submitted` | 都道府県ID、四択の並び、選択、位置と名前の各初回正誤 |
| `learning_activity` / `support_used` | 置いた場所と試行順、地方拡大、ヒント |
| `time_interval_closed` | 表示中の学習時間。タブの非表示時と3分間の無操作時に計測を止めます |

完了または中断した記録を同期し、通信失敗時はブラウザから再送できます。途中のコースは同じブラウザで再開できます。学習開始時にホームと未連携だった記録は、その端末で確認できます。

地図データの出典は国土地理院「地球地図日本」です。[Data of Japan](https://github.com/dataofjapan/land) の変換データを簡略化し、小さな島の一部を省略しています。沖縄は全国地図の別枠に拡大表示します。
