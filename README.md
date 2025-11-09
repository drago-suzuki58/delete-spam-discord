# Delete Spam Discord Bot

Discord メッセージの削除を、柔軟な条件指定で自動化する Bot です。

## 概要

主な特徴:
- 複数の条件タイプをサポート(サーバー、チャンネル、ユーザー、ロール、時刻など)
- AND/OR 演算子で条件を柔軟に組み合わせ可能
- ネストされた条件グループで複雑なロジックを表現
- ドライランで削除対象を事前確認
- 安全機能(最大削除件数制限、API 呼び出し間隔制御)
- CLI インターフェースで簡単に実行

## セットアップ

### 1. Discord Bot Token の取得

[Discord Developer Portal](https://discord.com/developers/applications) から Bot を作成し、トークンを取得

### 2. 依存関係のインストール

```bash
pip install .
```

または

```bash
uv sync
```

### 3. Token の設定

`del_spam/config.py`　を作成し、以下のように Bot トークンを設定

`del_spam/sample_config.py` を参考にしてください。

```python
DISCORD_TOKEN: str = "YOUR_DISCORD_TOKEN_HERE"
```

### 4. Bot の権限設定

Discord Developer Portal で、　Bot に以下の権限を付与

- `Read Messages/View Channels`
- `Read Message History`
- `Manage Messages`

### 5. 削除ルールの定義

`del_spam/config.py` の `DELETE_RULES` に、削除ルールを定義

```python
DELETE_RULES = {
    "rule_name": {
        "description": "このルールの説明",
        "enabled": True,  # False にするとこのルールは実行されません
        "conditions": {
            "operator": "AND", # または "OR"
            "filters": [
                # フィルター定義
            ]
        }
    }
}
```

## フィルタータイプと演算子

### フィルタータイプ

| タイプ | 説明 | 対応演算子 |
|--------|------|----------|
| `guild` | Discord サーバー ID で絞り込み | IN, NOT_IN, EQUALS, NOT_EQUALS |
| `channel` | チャンネル ID で絞り込み | IN, NOT_IN, EQUALS, NOT_EQUALS |
| `user` | ユーザー ID で絞り込み(メッセージ作成者) | IN, NOT_IN, EQUALS, NOT_EQUALS |
| `role` | ロール ID で絞り込み(ユーザーが持つロール) | IN, NOT_IN, EQUALS, NOT_EQUALS |
| `message_id` | メッセージ ID で絞り込み(特定メッセージの指定) | IN, NOT_IN, EQUALS, NOT_EQUALS |
| `timestamp` | メッセージ作成時刻(UTC)で絞り込み | BETWEEN, AFTER, BEFORE |
| `content` | メッセージ内容で絞り込み | CONTAINS, NOT_CONTAINS, STARTS_WITH, ENDS_WITH, REGEX |
| `group` | 複数の条件をグループ化(ネストされた AND/OR) | AND, OR |

### 演算子

#### 単純な比較演算子

| 演算子 | 説明 | 使用例 | フィルタータイプ |
|--------|------|--------|---------|
| `IN` | 値がリストに**含まれる** | `"values": [123, 456]` | guild, channel, user, role, message_id |
| `NOT_IN` | 値がリストに**含まれない** | `"values": [123, 456]` | guild, channel, user, role, message_id |
| `EQUALS` | 値が**完全に一致** | `"values": 123` | guild, channel, user, role, message_id |
| `NOT_EQUALS` | 値が**一致しない** | `"values": 123` | guild, channel, user, role, message_id |

#### 範囲演算子(時刻用)

| 演算子 | 説明 | パラメータ | 使用例 |
|--------|------|----------|--------|
| `BETWEEN` | タイムスタンプが指定期間**内** | `start`, `end` | `"start": "2024-01-01T00:00:00"`, `"end": "2024-01-31T23:59:59"` |
| `AFTER` | タイムスタンプが指定時刻**以降** | `start` | `"start": "2024-01-01T00:00:00"` |
| `BEFORE` | タイムスタンプが指定時刻**以前** | `end` | `"end": "2024-01-01T00:00:00"` |

#### 文字列演算子(content 用)

| 演算子 | 説明 | 使用例 |
|--------|------|--------|
| `CONTAINS` | 文字列を**含む** | `"values": ["spam", "ad"]` → "spam" または "ad" を含む |
| `NOT_CONTAINS` | 文字列を**含まない** | `"values": ["important"]` → "important" を含まない |
| `STARTS_WITH` | 文字列で**始まる** | `"values": [">>>"]` → ">>>" で始まる |
| `ENDS_WITH` | 文字列で**終わる** | `"values": ["!!!"]` → "!!!" で終わる |
| `REGEX` | 正規表現で**マッチ** | `"values": ["^\\[AUTO\\].*"]` → 正規表現にマッチ |

## 設定例

### 例1: 特定チャンネルの全メッセージを削除

```python
"rule_1_simple": {
    "description": "特定チャンネルの全メッセージ削除",
    "enabled": True,
    "conditions": {
        "operator": "AND",
        "filters": [
            {
                "type": "guild",
                "operator": "EQUALS",
                "values": 123456789
            },
            {
                "type": "channel",
                "operator": "EQUALS",
                "values": 987654321
            }
        ]
    }
}
```

### 例2: 特定ユーザーの特定期間のメッセージを削除

```python
"rule_2_complex_and": {
    "description": "特定ユーザーの特定期間のメッセージを削除",
    "enabled": True,
    "conditions": {
        "operator": "AND",
        "filters": [
            {
                "type": "guild",
                "operator": "EQUALS",
                "values": 123456789
            },
            {
                "type": "user",
                "operator": "IN",
                "values": [111111111, 222222222]
            },
            {
                "type": "timestamp",
                "operator": "BETWEEN",
                "start": "2024-01-01T00:00:00",
                "end": "2024-01-31T23:59:59"
            }
        ]
    }
}
```

### 例3: 特定キーワードを含むメッセージを削除

```python
"rule_8_content_filter": {
    "description": "特定のキーワードを含むメッセージを削除",
    "enabled": True,
    "conditions": {
        "operator": "AND",
        "filters": [
            {
                "type": "guild",
                "operator": "EQUALS",
                "values": 123456789
            },
            {
                "type": "content",
                "operator": "CONTAINS",
                "values": ["spam", "advertisement", "scam"]
            }
        ]
    }
}
```

### 例4: ネストされた複雑な条件(複数サーバーの複数ユーザー OR 特定チャンネル)

```python
"rule_4_nested": {
    "description": "ネストされた条件",
    "enabled": True,
    "conditions": {
        "operator": "AND",
        "filters": [
            {
                "type": "group",
                "operator": "OR",
                "conditions": [
                    {
                        "type": "guild",
                        "operator": "IN",
                        "values": [123456789, 987654321]
                    },
                    {
                        "type": "channel",
                        "operator": "EQUALS",
                        "values": 555555555
                    }
                ]
            },
            {
                "type": "timestamp",
                "operator": "BEFORE",
                "end": "2024-01-01T00:00:00"
            }
        ]
    }
}
```

### 例5: 特定ユーザーのメッセージは除外して削除

```python
"rule_7_with_exclusion": {
    "description": "ほぼすべてを削除するが、特定ユーザーのメッセージは除外",
    "enabled": True,
    "conditions": {
        "operator": "AND",
        "filters": [
            {
                "type": "guild",
                "operator": "EQUALS",
                "values": 123456789
            },
            {
                "type": "channel",
                "operator": "EQUALS",
                "values": 987654321
            },
            {
                "type": "user",
                "operator": "NOT_IN",
                "values": [666666666, 777777777]
            }
        ]
    }
}
```

## AND/OR 演算子

### トップレベルの演算子

条件グループの `operator` フィールドで、すべてのフィルターを AND で結合するか、OR で結合するかを指定します。

```python
"conditions": {
    "operator": "AND",  # すべてのフィルターが満たされる必要がある
    # または
    "operator": "OR",   # いずれかのフィルターが満たされればよい
    "filters": [...]
}
```

### ネストされたグループ

`type: "group"` を使用することで、フィルターをグループ化し、複雑な条件を作成できます。

```python
{
    "type": "group",
    "operator": "OR",
    "conditions": [
        # グループ内のフィルター
    ]
}
```

例: (A AND B) OR C の条件

```python
"conditions": {
    "operator": "OR",
    "filters": [
        {
            "type": "group",
            "operator": "AND",
            "conditions": [
                {"type": "guild", "operator": "EQUALS", "values": 123},
                {"type": "user", "operator": "EQUALS", "values": 456}
            ]
        },
        {
            "type": "channel",
            "operator": "EQUALS",
            "values": 789
        }
    ]
}
```

## 安全機能

### ドライラン(DRY_RUN)

`DRY_RUN = True` にすると、実際には削除せず、削除対象のメッセージを表示のみします。

```python
DRY_RUN = True  # True: 削除対象を表示のみ、False: 実際に削除
```

新しいルールを作成したときは、必ずドライランで削除対象を確認してから、`DRY_RUN = False` に変更することを推奨します。

### 最大削除件数制限(MAX_DELETIONS_PER_RUN)

誤設定による大量削除を防ぐため、1回の実行で削除できる最大メッセージ数を制限します。

```python
MAX_DELETIONS_PER_RUN = 1000  # 1回の実行で最大 1000 件まで削除
```

### バッチサイズ(BATCH_SIZE)

1回の API 呼び出しで処理するメッセージ数を指定します。

```python
BATCH_SIZE = 100  # 100 件ずつ処理
```

### API 呼び出し間隔(API_CALL_INTERVAL)

Discord の Rate Limit 対策として、API 呼び出し間の待機時間(秒)を指定します。

```python
API_CALL_INTERVAL = 0.5  # 0.5 秒待機
```

## 注意事項

- このツールは削除対象のメッセージを復元できません。DRY RUNで必ず確認してから実行してください。
- Discord の Terms of Service を遵守した用途でのみ使用してください。
- 大量削除時は Discord の Rate Limit に注意してください。
- Bot が削除できるのは、自分が削除権限を持つメッセージのみです。

## カスタマイズ

### 新しいフィルタータイプを追加する場合

1. `del_spam/filter.py` の `FilterType` Enum に新しいタイプを追加
2. `Filter` クラスに対応する `_match_*` メソッドを実装
3. README のフィルタータイプテーブルを更新

### 新しい演算子を追加する場合

1. `del_spam/filter.py` の `Operator` Enum に新しい演算子を追加
2. 各 `_match_*` メソッドで演算子を処理するロジックを実装
3. README の演算子テーブルを更新
