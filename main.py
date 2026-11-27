import os
import random
import pyxel


class App:

  def __init__(self):
    # 画面サイズを 208x208 に設定、マウスカーソルは初期非表示
    pyxel.init(208, 208, title="Pixel Game - Pyxel", fps=60)
    pyxel.mouse(False)

    # プレイヤーの初期状態
    self.x = 64
    self.y = 98
    self.width = 32
    self.height = 32

    self.direction = "down"  # "down", "up", "left", "right"
    self.moving = False
    self.was_moving = False

    self.frame_x = 0
    self.frame_y = 0
    self.anim_timer = 0
    # 【アニメーション速度を1.5倍に高速化 (6フレーム毎 → 4フレーム毎)】
    self.anim_speed = 4
    self.idle_step_count = 0

    # 調整モードの表示フラグ（初期値は非表示）
    self.debug_mode = False
    self.debug_jump_mode = False  # ← ★追加：デバッグ中のテーブル表示切替（False:歩行, True:ジャンプ）
    # パレット書き出し完了メッセージの表示タイマー  <-- ★ここを追加
    self.export_msg_timer = 0
    self.copy_msg_timer = 0  # ← ★追加：テーブルコピー完了メッセージ表示タイマー

    # ドロン直後のアイドルアニメーションスキップ用フラグ
    self.skip_idle = False

    # 【移動量テーブルの拡張：各方向ごとに「主方向(Main)」と「副方向(Sub)」の2軸を設定】
    # --- UP 時 ---
    self.up_main = list((4, 3, 4, 4, 3, 4))  # 上方向への移動量 (Y)
    self.up_sub = list((1, 2, 0, -1, -2, 0))  # 同時にずらす横方向の量 (X)
    # --- DOWN 時 ---
    self.down_main = list((5, 4, 3, 5, 4, 3))  # 下方向への移動量 (Y)
    self.down_sub = list((0, 0, 2, 0, 0, -2))  # 同時にずらす横方向の量 (X)
    # --- LEFT 時 ---
    self.left_main = list((5, 7, 5, 6, 5, 5))  # 左方向への移動量 (X)
    self.left_sub = list((0, 0, 0, 0, 0, 0))  # 同時にずらす縦方向の量 (Y)
    # --- RIGHT 時 ---
    self.right_main = list((5, 7, 5, 6, 5, 5))  # 右方向への移動量 (X)
    self.right_sub = list((0, 0, 0, 0, 0, 0))  # 同時にずらす縦方向の量 (Y)

    # --- ワープアニメーション用の状態管理 ---
    self.state = "NORMAL"  # "NORMAL", "WARP_OUT", "WARP_IN"

    # 独立したタイムライン用変数
    self.dron_frame = 0.0  # ドロン用フレーム (0 〜 12)
    self.dron_timer = 0  # ドロンのコマ送りタイマー

    self.smoke_frame = 0.0  # ケムリ用フレーム (0 〜 12)
    self.smoke_timer = 0  # ケムリのコマ送りタイマー
    self.smoke_started = False  # 煙を遅延スタートさせるためのフラグ

    self.max_dron_frame = 12
    self.max_smoke_frame = 12

    # BGMのロードと再生
    try:
      pyxel.load("karakusaWalk.pyxres")  # BGMを保存した .pyxres を指定
      pyxel.playm(0, loop=True)  # ミュージック 0 番をループ再生する場合
    except Exception as e:
      print(f"BGMロードエラー: {e}")

    # 【画像の読み込み（.pyxres の後に読み込んで上書きを防止）】
    try:
      # Bank 0: 歩行グラフィック（左側：x=0）
      pyxel.image(0).load(0, 0, "karakusa_32_F.png")
      pyxel.image(0).load(0, 64, "karakusa_32_B.png")
      pyxel.image(0).load(0, 128, "karakusa_32_Jmp.png") # ← ★追加：ジャンプ画像（256x64）
      pyxel.image(0).load(0, 192, "karakusa_32_R.png")

      # Bank 0: 各方向の停止・アイドルグラフィック（右側：x=96）
      pyxel.image(0).load(96, 0, "karakusa_32_Fstp.png")
      pyxel.image(0).load(96, 64, "karakusa_32_Bstp.png")
      pyxel.image(0).load(96, 192, "karakusa_32_Rstp.png")

      # Bank 1: エフェクト用（縦2段のスプライトシート）
      pyxel.image(1).load(0, 0, "karakusa_32_DronF.png")
      pyxel.image(1).load(0, 64, "karakusa_32_Smoke.png")

      # Bank 2: タイルセット画像
      pyxel.image(2).load(0, 0, "map_tileset.png")
      # Tilemap 0: 配置データ (.tmx) を読み込み、画像バンク2番と紐付け
      pyxel.tilemaps[0] = pyxel.Tilemap.from_tmx("map.tmx", 0)
      pyxel.tilemaps[0].imgsrc = 2
    except Exception as e:
      print(f"画像ロードエラー: {e}")

    # ==========================================================
    # 【追加】タイル判定と重力の設定
    # ==========================================================
    # map_tileset.png 上のタイル座標 (横インデックス, 縦インデックス) ※0始まり
    # 例: 左上から2番目なら (1, 0)、2段目の左端なら (0, 1)
    # 床・壁のタイル定義
    self.SOLID_TILES = [
       (0, 2) 
       ] 

    # はしご（階段）のタイル定義（中央スナップ＆昇降ロックあり）
    self.STAIR_TILES = [
       (12, 1), (15, 1), (13, 1), (14, 1), (10, 1), (11, 1)
    ]

    # 上下左右に自由移動できるタイル定義（重力無効・スナップなし）
    self.FREE_MOVE_TILES = [
       (9, 2), (0, 1), (1, 1)
    #   (9, 2)
    ]

    # 重力設定
    self.vy = 0.0             # 落下速度
    self.gravity = 0.4        # 重力の強さ
    self.max_fall_speed = 6.0 # 最大落下速度
    self.on_ground = False    # 接地フラグ
    self.on_stair = False     # 階段接触フラグ
    self.on_free_tile = False # 自由移動タイル接触フラグ
    self.climbing = False     # はしご昇降中フラグ
    self.lock_stair_up = False # 登りきった直後の上入力ロック
    self.lock_stair_dn = False # 降りきった直後の下入力ロック
    self.stair_top_hold = False # ハシゴを登りきった直後の1px高い位置をキープ
    self.lock_free_up = False   # ← ★追加：自由移動エリアの上端ロック
    self.lock_free_dn = False   # ← ★追加：自由移動エリアの下端ロック
    self.clicked_tile = (0, 0) # ← ★追加：クリックした場所のタイルID (u, v)
    self.clicked_pos = None    # ← ★追加：クリックしたマップ上のマス座標 (tx, ty)

    # --- ★追加：ジャンプ用の状態管理（14コマ固定軌道テーブル方式） ---
    self.is_jumping = False    # ジャンプ一連動作中フラグ (0〜13コマ)
    self.jump_frame = 0        # ジャンプの現在コマ (0 〜 13)
    self.jump_timer = 0        # ジャンプのコマ送りタイマー
    self.jump_speed = 3        # ジャンプのコマ送り速度（フレーム数）
    self.jump_dir = 1          # 1: 右向きジャンプ, -1: 左向きジャンプ
    self.jump_origin_x = 0     # ← ★追加：デバッグ時のジャンプ開始基準X座標
    self.jump_origin_y = 0     # ← ★追加：デバッグ時のジャンプ開始基準Y座標

    # 14コマそれぞれの移動量 (0〜3:踏ん張り, 4〜7:空中移動, 8〜13:着地硬直)
    # ※数値はデバッグしながらお好みで微調整できます
    # --- ジャンプ移動量テーブル ---
    self.jump_dx = [0, 0, 0, 11, 8, 11, 4, 5, 7, 4, 1, 2, 2, 4]
    self.jump_dy = [0, 0, 0, 0, -11, -4, 4, 11, 0, 0, 0, 0, 0, 0]

    pyxel.run(self.update, self.draw)

  # --- 現在のパレットをAseprite用(.gpl)に書き出すヘルパー関数 ---
  def export_palette_for_aseprite(self, filename="pyxel_palette.gpl"):
    lines = [
        "GIMP Palette",
        "Name: Pyxel Palette",
        "Columns: 16",
        "#",
    ]
    for i, col in enumerate(pyxel.colors):
      r = (col >> 16) & 0xFF
      g = (col >> 8) & 0xFF
      b = col & 0xFF
      lines.append(f"{r:3d} {g:3d} {b:3d}\tColor {i}")
    content = "\n".join(lines) + "\n"

    # Webブラウザ環境（Pyodide）の場合はブラウザ経由でダウンロード
    try:
      import js # type: ignore
      blob = js.Blob.new([content], {"type": "text/plain;charset=utf-8"})
      url = js.URL.createObjectURL(blob)
      a = js.document.createElement("a")
      a.href = url
      a.download = filename
      a.click()
      js.URL.revokeObjectURL(url)
      print(f"ブラウザからダウンロードしました: {filename}")
      self.export_msg_timer = 120
      return
    except ImportError:
      pass  # PCの通常Python環境の場合は下の処理へ進む

    # PCの通常Python環境の場合はローカルに保存
    try:
      base_dir = os.path.dirname(os.path.abspath(__file__))
      save_path = os.path.join(base_dir, filename)
      with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)
      print(f"パレットを書き出しました: {save_path}")
      self.export_msg_timer = 120
    except Exception as e:
      print(f"パレット書き出しエラー: {e}")

  # --- 現在の移動量テーブル定義コードをクリップボードにコピーするヘルパー関数 ---
  def copy_tables_to_clipboard(self):
    code_text = (
        f"    # --- UP 時 ---\n"
        f"    self.up_main = list({tuple(self.up_main)})\n"
        f"    self.up_sub = list({tuple(self.up_sub)})\n"
        f"    # --- DOWN 時 ---\n"
        f"    self.down_main = list({tuple(self.down_main)})\n"
        f"    self.down_sub = list({tuple(self.down_sub)})\n"
        f"    # --- LEFT 時 ---\n"
        f"    self.left_main = list({tuple(self.left_main)})\n"
        f"    self.left_sub = list({tuple(self.left_sub)})\n"
        f"    # --- RIGHT 時 ---\n"
        f"    self.right_main = list({tuple(self.right_main)})\n"
        f"    self.right_sub = list({tuple(self.right_sub)})\n\n"
        f"    # --- ジャンプ移動量テーブル ---\n"
        f"    self.jump_dx = {self.jump_dx}\n"
        f"    self.jump_dy = {self.jump_dy}\n"
    )

    print("=== 移動量テーブル定義コード ===")
    print(code_text)

    # 1. Webブラウザ環境（Pyodide）の場合
    try:
      import js  # type: ignore
      js.navigator.clipboard.writeText(code_text)
      self.copy_msg_timer = 120
      return
    except Exception:
      pass

    # 2. PC環境（tkinter または OS標準コマンドでクリップボードへコピー）
    try:
      import tkinter as tk
      root = tk.Tk()
      root.withdraw()
      root.clipboard_clear()
      root.clipboard_append(code_text)
      root.update()
      root.destroy()
      self.copy_msg_timer = 120
    except Exception as e:
      print(f"クリップボードコピーエラー: {e}")

  # --- 縦2段（1行8個）のシートから正しい (u, v) を計算するヘルパー関数 ---
  def get_effect_uv(self, frame_idx):
    if frame_idx < 8:
      u = (frame_idx % 8) * self.width
      v = 0
    else:
      u = ((frame_idx - 8) % 8) * self.width
      v = 32
    return u, v

  def get_smoke_uv(self, frame_idx):
    if frame_idx < 8:
      u = (frame_idx % 8) * self.width
      v = 64
    else:
      u = ((frame_idx - 8) % 8) * self.width
      v = 96
    return u, v

  # --- 現在のフレーム(frame_x, frame_y)を 0〜5 のインデックスに変換するヘルパー関数 ---
  def get_anim_index(self):
    if self.frame_y == 0:
      return self.frame_x
    else:
      return self.frame_x + 3

  # --- 0〜5 のインデックスを (frame_x, frame_y) に設定するヘルパー関数 ---
  def set_anim_index(self, idx):
    idx = idx % 6
    self.frame_x = idx % 3
    self.frame_y = idx // 3

  # --- 指定ピクセル座標にあるタイル種別を取得 ---
  def get_tile_at(self, px, py):
    tx = int(px // 8)
    ty = int(py // 8)
    if 0 <= tx < 26 and 0 <= ty < 26:  # 208 / 8 = 26マス
      return pyxel.tilemaps[0].pget(tx, ty)
    return (0, 0)

  # --- プレイヤーの当たり判定枠（足元・胴体）を取得 ---
  def get_hitbox(self, x, y):
    # 32x32画像のうち、左右8px・上8pxを削った内側を当たり判定にする
    return (x + 8, y + 8, x + self.width - 9, y + self.height - 1)

  # --- 指定座標で「床・壁」または「階段」に触れているか判定 ---
  def check_tile_collision(self, x, y, target_tiles):
    x1, y1, x2, y2 = self.get_hitbox(x, y)
    # 判定枠の四隅と中間点を8px刻みでチェック
    for check_y in range(int(y1), int(y2) + 1, 4):
      for check_x in range(int(x1), int(x2) + 1, 4):
        if self.get_tile_at(check_x, check_y) in target_tiles:
          return True
    # 右端・下端のラインも確実にチェック
    for check_y in [int(y1), int(y2)]:
      for check_x in [int(x1), int(x2)]:
        if self.get_tile_at(check_x, check_y) in target_tiles:
          return True
    return False

  # --- 触れているはしご全体（左右の隣接タイルも含む）の中央X座標を計算 ---
  def get_stair_center_x(self):
    x1, y1, x2, y2 = self.get_hitbox(self.x, self.y)
    player_center_x = (x1 + x2) / 2.0
    hit_tiles = []

    # 1. プレイヤーの体〜足元16px下が触れているはしごタイル(tx, ty)を集める
    for check_y in range(int(y1), int(y2) + 17, 2):
      for check_x in range(int(x1), int(x2) + 1, 2):
        tx = int(check_x // 8)
        ty = int(check_y // 8)
        if 0 <= tx < 26 and 0 <= ty < 26:
          if pyxel.tilemaps[0].pget(tx, ty) in self.STAIR_TILES:
            if (tx, ty) not in hit_tiles:
              hit_tiles.append((tx, ty))

    if hit_tiles:
      # プレイヤーの中心X座標に最も近いタイルを基準にする（端の誤検出を防止）
      base_tx, base_ty = min(
          hit_tiles, key=lambda t: abs((t[0] * 8 + 4) - player_center_x)
      )
      left_tx = base_tx
      right_tx = base_tx

      # 左隣もはしごタイルなら左端を広げる
      if left_tx - 1 >= 0 and pyxel.tilemaps[0].pget(left_tx - 1, base_ty) in self.STAIR_TILES:
        left_tx -= 1
      # 右隣もはしごタイルなら右端を広げる
      if right_tx + 1 < 26 and pyxel.tilemaps[0].pget(right_tx + 1, base_ty) in self.STAIR_TILES:
        right_tx += 1

      # はしご全体の左端ピクセルと右端ピクセルの中間を計算し、1px左に補正
      min_px = left_tx * 8
      max_px = (right_tx + 1) * 8
      center_px = (min_px + max_px) / 2.0
      return int(round(center_px - self.width / 2.0)) - 1

    return self.x

  def update(self):
    # Qキーで終了
    if pyxel.btnp(pyxel.KEY_Q):
      pyxel.quit()

    # ★ここを追加（メッセージ表示タイマーを減らす）
    if self.export_msg_timer > 0:
      self.export_msg_timer -= 1
    if self.copy_msg_timer > 0:
      self.copy_msg_timer -= 1

    # --- セレクトボタン（押し始め）で調整モードの表示・非表示をトグル ---
    if (
        pyxel.btnp(pyxel.GAMEPAD1_BUTTON_BACK)
        or pyxel.btnp(pyxel.KEY_TAB)
        or pyxel.btnp(pyxel.KEY_BACKSPACE)
    ):
      self.debug_mode = not self.debug_mode
      pyxel.mouse(self.debug_mode)  # 調整モード中だけカーソル表示

      try:
        if self.debug_mode:
          pyxel.stop()  # 調整モードに入ったらBGM停止
        else:
          pyxel.playm(0, loop=True)  # 調整モードを抜けたらBGM再開
      except Exception:
        pass

    # --- 調整モード表示中のみマウス操作による数値調整を受け付ける ---
    if self.debug_mode:
      mx, my = pyxel.mouse_x, pyxel.mouse_y
      left_clicked = pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
      right_clicked = pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT)

      # パレット書き出しボタン (EXP PAL) のクリック判定
      if left_clicked and (85 <= mx <= 125) and (84 <= my <= 94):
        self.export_palette_for_aseprite()

      # ジャンプテーブル切り替えボタン (JMP TBL / WLK TBL) のクリック判定
      elif left_clicked and (128 <= mx <= 172) and (84 <= my <= 94):
        self.debug_jump_mode = not self.debug_jump_mode
        if self.debug_jump_mode:
          self.jump_frame = 0
          self.jump_origin_x = self.x
          self.jump_origin_y = self.y
          if self.direction not in ["left", "right"]:
            self.direction = "right"

      # ★追加：移動量テーブルコードのクリップボードコピーボタン (CPY TBL) のクリック判定
      elif left_clicked and (175 <= mx <= 207) and (84 <= my <= 94):
        self.copy_tables_to_clipboard()

      # 移動量テーブルの数値調整クリック判定
      elif (left_clicked or right_clicked) and (50 <= mx <= 195) and (2 <= my <= 82):
        delta = 1 if left_clicked else -1

        # 【ジャンプテーブル表示中】のクリック調整（7コマずつ2段構成）
        if self.debug_jump_mode:
          row_idx = (my - 2) // 10
          # row 0: JMP-X(0〜6), row 1: JMP-Y(0〜6), row 3: JMP-X(7〜13), row 4: JMP-Y(7〜13)
          if row_idx in (0, 1, 3, 4):
            col_idx = (mx - 76) // 16
            if 0 <= col_idx < 7:
              frame_idx = col_idx if row_idx in (0, 1) else col_idx + 7
              if row_idx in (0, 3):
                self.jump_dx[frame_idx] += delta
                print(f"Updated jump_dx[{frame_idx}]: {self.jump_dx}")
              else:
                self.jump_dy[frame_idx] += delta
                print(f"Updated jump_dy[{frame_idx}]: {self.jump_dy}")

              # ★追加：いじったコマ(frame_idx)にキャラクターの表示コマも合わせ、基準位置からの移動を即座に反映！
              self.jump_frame = frame_idx
              dir_sign = -1 if self.direction == "left" else 1
              self.x = self.jump_origin_x + sum(self.jump_dx[:self.jump_frame + 1]) * dir_sign
              self.y = self.jump_origin_y + sum(self.jump_dy[:self.jump_frame + 1])

        # 【通常歩行テーブル表示中】のクリック調整
        else:
          if 85 <= mx <= 165:
            row_idx = (my - 2) // 10
            if 0 <= row_idx < 8:
              idx = (mx - 85) // 8
              if 0 <= idx < 6:
                target_tables = [
                    (self.up_main, "UP Main"),
                    (self.up_sub, "UP Sub"),
                    (self.down_main, "DOWN Main"),
                    (self.down_sub, "DOWN Sub"),
                    (self.left_main, "LEFT Main"),
                    (self.left_sub, "LEFT Sub"),
                    (self.right_main, "RIGHT Main"),
                    (self.right_sub, "RIGHT Sub"),
                ]
                t, name = target_tables[row_idx]
                t[idx] += delta
                print(f"Updated {name}: {t}")

      # それ以外の場所を左クリックしたら、その位置のタイルパターンを取得して記憶する
      elif left_clicked:
        self.clicked_tile = self.get_tile_at(mx, my)
        self.clicked_pos = (int(mx // 8), int(my // 8))

    # --- 1. 消えるときの演出 (WARP_OUT) ---
    if self.state == "WARP_OUT":
      self.dron_timer += 1
      dron_speed = 15 if int(self.dron_frame) >= 10 else 4

      if self.dron_timer >= dron_speed:
        self.dron_timer = 0
        if self.dron_frame <= self.max_dron_frame:
          self.dron_frame += 1

        if int(self.dron_frame) >= 8:
          self.smoke_started = True

      if self.smoke_started:
        self.smoke_timer += 1
        if self.smoke_timer >= 5:
          self.smoke_timer = 0
          if self.smoke_frame <= self.max_smoke_frame:
            self.smoke_frame += 1

      if (
          self.dron_frame > self.max_dron_frame
          and self.smoke_frame > self.max_smoke_frame
      ):
        max_x = max(0, 208 - self.width)
        max_y = max(0, 208 - self.height)

        # 床に埋まらない安全な座標を最大100回まで抽選する
        for _ in range(100):
          cand_x = random.randint(0, max_x)
          cand_y = random.randint(0, max_y)
          if not self.check_tile_collision(cand_x, cand_y, self.SOLID_TILES):
            self.x = cand_x
            self.y = cand_y
            break

        self.state = "WARP_IN"
        self.vy = 0.0  # ← ★ここを追加
        self.dron_frame = float(self.max_dron_frame)
        self.dron_timer = 0
        self.smoke_frame = 0.0
        self.smoke_timer = 0
        self.smoke_started = True
      return

    # --- 2. 現れるときの演出 (WARP_IN) ---
    elif self.state == "WARP_IN":
      self.dron_timer += 1
      if self.dron_timer >= 4:
        self.dron_timer = 0
        if self.dron_frame > 0:
          self.dron_frame -= 1

      self.smoke_timer += 1
      if self.smoke_timer >= 5:
        self.smoke_timer = 0
        if self.smoke_frame <= self.max_smoke_frame:
          self.smoke_frame += 1

      # 煙が最後まで再生しきったら通常状態へ（前向きの停止パターン最終コマにセット）
      if self.smoke_frame > self.max_smoke_frame:
        pyxel.stop(0)  # ドロン音を停止
        self.state = "NORMAL"
        self.direction = "down"  # 前向きにリセット
        self.frame_x = 2  # 停止シート前向き行の最後のコマ(x=2)
        self.frame_y = 1  # 停止シートの2段目(v=1)
        self.anim_timer = 0
        self.idle_step_count = 6  # アニメーションが既に完了した状態にする
        self.skip_idle = True  # ドロン直後の追加アニメーションをスキップ
        self.moving = False  # キー押しっぱなしによる誤作動を防ぐため移動状態を強制解除
        self.was_moving = False  # 状態変化フラグもリセット
      return

    # --- 3. 通常時の処理（移動・ワープトリガー） ---
    is_warp = pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(
        pyxel.GAMEPAD1_BUTTON_A
    )
    if is_warp:
      self.state = "WARP_OUT"
      self.dron_frame = 0.0
      self.dron_timer = 0
      self.smoke_frame = 0.0
      self.smoke_timer = 0
      self.smoke_started = False
      pyxel.play(0, 5, loop=True)  # サウンド5番をループ再生
      return

    # ==========================================================
    # 【デバッグモード中】：十字キーで向き変更、右/左ボタンで1コマ送り・戻し
    # ==========================================================
    if self.debug_mode:
      self.moving = False

      # 十字キー（押し始め）で向きを切り替え、0コマ目に戻す
      if (
          pyxel.btnp(pyxel.KEY_UP)
          or pyxel.btnp(pyxel.KEY_W)
          or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP)
      ):
        self.direction = "up"
        self.set_anim_index(0)
      elif (
          pyxel.btnp(pyxel.KEY_DOWN)
          or pyxel.btnp(pyxel.KEY_S)
          or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)
      ):
        self.direction = "down"
        self.set_anim_index(0)
      elif (
          pyxel.btnp(pyxel.KEY_LEFT)
          or pyxel.btnp(pyxel.KEY_A)
          or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)
      ):
        self.direction = "left"
        self.set_anim_index(0)
      elif (
          pyxel.btnp(pyxel.KEY_RIGHT)
          or pyxel.btnp(pyxel.KEY_D)
          or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)
      ):
        self.direction = "right"
        self.set_anim_index(0)

      # コマ送り（右ボタン：パッドB / Xキー）
      step_next = pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B) or pyxel.btnp(pyxel.KEY_X)
      # コマ戻し（左ボタン：パッドY / Zキー）
      step_prev = pyxel.btnp(pyxel.GAMEPAD1_BUTTON_Y) or pyxel.btnp(pyxel.KEY_Z)

      if step_next:
        if self.debug_jump_mode:
          self.jump_frame = (self.jump_frame + 1) % 14
          dir_sign = -1 if self.direction == "left" else 1
          self.x = self.jump_origin_x + sum(self.jump_dx[:self.jump_frame + 1]) * dir_sign
          self.y = self.jump_origin_y + sum(self.jump_dy[:self.jump_frame + 1])
        else:
          anim_idx = self.get_anim_index()
          if self.direction == "up":
            self.y -= self.up_main[anim_idx]
            self.x += self.up_sub[anim_idx]
          elif self.direction == "down":
            self.y += self.down_main[anim_idx]
            self.x += self.down_sub[anim_idx]
          elif self.direction == "left":
            self.x -= self.left_main[anim_idx]
            self.y += self.left_sub[anim_idx]
          elif self.direction == "right":
            self.x += self.right_main[anim_idx]
            self.y += self.right_sub[anim_idx]
          self.set_anim_index(anim_idx + 1)

      elif step_prev:
        if self.debug_jump_mode:
          self.jump_frame = (self.jump_frame - 1) % 14
          dir_sign = -1 if self.direction == "left" else 1
          self.x = self.jump_origin_x + sum(self.jump_dx[:self.jump_frame + 1]) * dir_sign
          self.y = self.jump_origin_y + sum(self.jump_dy[:self.jump_frame + 1])
        else:
          prev_idx = (self.get_anim_index() - 1) % 6
          self.set_anim_index(prev_idx)
          if self.direction == "up":
            self.y += self.up_main[prev_idx]
            self.x -= self.up_sub[prev_idx]
          elif self.direction == "down":
            self.y -= self.down_main[prev_idx]
            self.x -= self.down_sub[prev_idx]
          elif self.direction == "left":
            self.x += self.left_main[prev_idx]
            self.y -= self.left_sub[prev_idx]
          elif self.direction == "right":
            self.x -= self.right_main[prev_idx]
            self.y -= self.right_sub[prev_idx]

    # ==========================================================
    # 【通常モード中】：これまでの連続移動処理
    # ==========================================================
    else:
      self.was_moving = self.moving
      self.moving = False

      # --- ★追加：ジャンプ中の14コマ軌道＆アニメーション処理 ---
      if self.is_jumping:
        is_jump_btn = pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)
        any_dir_btn = (
            pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP)
            or pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)
            or pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)
            or pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)
        )

        # 9コマ目以降（index 8〜13の着地モーション中）で地面に着いているとき
        if self.jump_frame >= 8:
          on_floor = (
              (self.y + 2 > 208 - self.height)
              or self.check_tile_collision(self.x, self.y + 2, self.SOLID_TILES)
              or self.check_tile_collision(self.x, self.y, self.FREE_MOVE_TILES)
          )
          if on_floor:
            # ① ジャンプキーなら連続ジャンプへ
            if is_jump_btn:
              self.jump_frame = 0
              self.jump_timer = 0
              if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
                self.direction = "left"
                self.jump_dir = -1
              elif pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
                self.direction = "right"
                self.jump_dir = 1
              try:
                pyxel.play(0, 0)
              except Exception:
                pass
              return
            # ② 方向キーが押されたら着地モーションを即キャンセルして通常移動・ハシゴ処理へ進む
            elif any_dir_btn:
              self.is_jumping = False
              self.jump_frame = 0
              self.skip_idle = True

        self.jump_timer += 1
        if self.jump_timer >= self.jump_speed:
          self.jump_timer = 0
          self.jump_frame += 1

          # 14コマ目(index 13)まで再生し終わったらジャンプ終了
          if self.jump_frame >= 14:
            self.is_jumping = False
            self.jump_frame = 0
            self.skip_idle = True
            return

          # 現在のコマの移動量を取得
          dx = self.jump_dx[self.jump_frame] * self.jump_dir
          dy = self.jump_dy[self.jump_frame]

          # X方向の移動（壁にぶつかったらそこで止まる）
          if dx != 0:
            step_x = 1 if dx > 0 else -1
            for _ in range(abs(dx)):
              if not self.check_tile_collision(self.x + step_x, self.y, self.SOLID_TILES):
                self.x += step_x
              else:
                break

          # Y方向の移動（上昇時は天井、下降時は床・自由移動エリアの着地判定）
          if dy < 0:
            for _ in range(abs(dy)):
              if self.y - 1 >= 0 and not self.check_tile_collision(self.x, self.y - 1, self.SOLID_TILES):
                self.y -= 1
              else:
                break
          elif dy > 0:
            for _ in range(abs(dy)):
              hit_solid = (self.y + 2 > 208 - self.height) or self.check_tile_collision(self.x, self.y + 2, self.SOLID_TILES)
              # 自由移動エリアから跳んだ場合、元の高さ（足元が自由移動エリアに接地する位置）で着地
              hit_free = self.check_tile_collision(self.x, self.y + 1, self.FREE_MOVE_TILES) and self.jump_frame >= 7
              if hit_solid or hit_free:
                # 地面に着地したら、即座に8コマ目（着地ショック吸収ポーズ）へ移行
                if self.jump_frame < 8:
                  self.jump_frame = 8
                break
              else:
                self.y += 1

          # 8コマ目(index 7)が終わった時点でまだ空中にいる場合（段差から飛び降りたときなど）は落下させる
          if self.jump_frame >= 8:
            on_floor = (self.y + 2 > 208 - self.height) or self.check_tile_collision(self.x, self.y + 2, self.SOLID_TILES) or self.check_tile_collision(self.x, self.y, self.FREE_MOVE_TILES)
            if not on_floor:
              # 地面に着くまで7コマ目（下降ポーズ）のまま真下へ落下する
              self.jump_frame = 7
              self.y += 4

        # ジャンプ中は画面端制限だけかけて通常歩行・重力をスキップ
        self.x = max(0, min(self.x, 208 - self.width))
        self.y = max(0, min(self.y, 208 - self.height))
        return

      # --- ★追加：ジャンプ開始トリガー（Zキー / ゲームパッドBボタン） ---
      is_jump_btn = pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)
      if is_jump_btn and (self.on_ground or self.on_free_tile or self.stair_top_hold) and not self.climbing:
        self.is_jumping = True
        self.jump_frame = 0  # 0コマ目（踏ん張り1コマ目）からスタート
        self.jump_timer = 0
        self.stair_top_hold = False
        # 現在の向きに応じてジャンプ方向を決定（上下を向いている場合は右向き基準）
        if self.direction == "left":
          self.jump_dir = -1
        else:
          self.direction = "right"
          self.jump_dir = 1
        try:
          pyxel.play(0, 0)
        except Exception:
          pass
        return

      # 1. 現在「階段」または「自由移動タイル (9,2)」に触れているかチェック（端4pxのカスりを除外し、登れる範囲と一致させる）
      sx1, sy1, sx2, sy2 = self.get_hitbox(self.x, self.y)
      self.on_stair = False
      check_y_list = list(range(int(sy1), int(sy2) + 1, 4)) + [int(sy2) + 1, int(sy2) + 2, int(sy2) + 3]
      for check_y in check_y_list:
        for check_x in range(int(sx1) + 4, int(sx2) - 3, 2):
          if self.get_tile_at(check_x, check_y) in self.STAIR_TILES:
            self.on_stair = True
            break
        if self.on_stair:
          break

      self.on_free_tile = self.check_tile_collision(self.x, self.y, self.FREE_MOVE_TILES)

      # 階段から完全に離れたら昇降モードを解除
      if not self.on_stair:
        self.climbing = False

      is_up = (
          pyxel.btn(pyxel.KEY_UP)
          or pyxel.btn(pyxel.KEY_W)
          or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP)
      )
      is_down = (
          pyxel.btn(pyxel.KEY_DOWN)
          or pyxel.btn(pyxel.KEY_S)
          or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)
      )
      is_left = (
          pyxel.btn(pyxel.KEY_LEFT)
          or pyxel.btn(pyxel.KEY_A)
          or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)
      )
      is_right = (
          pyxel.btn(pyxel.KEY_RIGHT)
          or pyxel.btn(pyxel.KEY_D)
          or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)
      )

      # 該当のキーを離したとき（またはハシゴに触れたとき）に上端ロックを解除する
      if not is_up:
        self.lock_stair_up = False
        self.lock_free_up = False
      if self.on_stair:
        self.lock_free_up = False
      if not is_down:
        self.lock_stair_dn = False
        self.lock_free_dn = False

      # 階段にも自由移動タイルにもいないとき、または上端ロック中は「上移動」を無効化
      if (not self.on_stair and not self.on_free_tile) or self.lock_stair_up or self.lock_free_up:
        is_up = False

      # 階段にも自由移動タイルにもいないとき、または自由移動エリアの下端ロック中は「下移動」を無効化
      if (not self.on_stair and not self.on_free_tile) or self.lock_free_dn:
        is_down = False

      # ハシゴを下りきった直後（lock_stair_dn中）に斜め下入力されているときは、左右移動だけをキャンセルして下へ歩き続ける（バタバタ防止）
      if self.lock_stair_dn and is_down:
        is_left = False
        is_right = False

      # 階段に触れている状態（または下キーで足元下にハシゴがあるとき）に上下キーを押したら「昇降モード」に入る
      if (self.on_stair or is_down) and (is_up or is_down):
        cx1, cy1, cx2, cy2 = self.get_hitbox(self.x, self.y)

        if is_up:
          can_climb_up = False
          up_check_y = list(range(int(cy1), int(cy2) + 1, 4)) + [int(cy2), int(cy2) + 1, int(cy2) + 2]
          for check_y in up_check_y:
            for check_x in range(int(cx1) + 4, int(cx2) - 3, 2):
              if self.get_tile_at(check_x, check_y) in self.STAIR_TILES:
                can_climb_up = True
                break
            if can_climb_up:
              break
          if can_climb_up:
            # まだ昇降モードに入っていなかった瞬間（掴まり始め）だけ中央にスナップさせる
            if not self.climbing:
              self.x = self.get_stair_center_x()
            self.climbing = True

        elif is_down and not self.lock_stair_dn:
          # 下に降りるとき：足元付近（左右2px内側）の1〜16px下にハシゴがあるかチェック
          can_climb_down = False
          for check_y in range(int(cy2) + 1, int(cy2) + 17, 2):
            for check_x in range(int(cx1) + 2, int(cx2) - 1, 2):
              if self.get_tile_at(check_x, check_y) in self.STAIR_TILES:
                can_climb_down = True
                break
          # 自由移動エリア外で、すでに体そのものがハシゴの途中にある場合もそのまま下へ降りる
          if not can_climb_down and not self.on_free_tile:
            for check_y in range(int(cy1), int(cy2) + 1, 4):
              for check_x in range(int(cx1) + 2, int(cx2) - 1, 2):
                if self.get_tile_at(check_x, check_y) in self.STAIR_TILES:
                  can_climb_down = True
                  break
          if can_climb_down:
            # まだ昇降モードに入っていなかった瞬間（降り始め）だけ中央にスナップさせ、1px下へ踏み出して確実にハシゴ判定に乗せる
            if not self.climbing:
              self.x = self.get_stair_center_x()
              self.y += 1
            self.climbing = True

      # 昇降モード中でも、上下キーを離して「左右キーだけ」を押したときは横が壁でなければ抜ける
      if self.climbing and not (is_up or is_down):
        if is_left and not self.check_tile_collision(self.x - 4, self.y, self.SOLID_TILES):
          self.climbing = False
        elif is_right and not self.check_tile_collision(self.x + 4, self.y, self.SOLID_TILES):
          self.climbing = False

      # 昇降モード中の場合：左右キー入力はロックするが、X座標の上書きはしない（Subテーブルの横揺れを活かすため）
      if self.climbing:
        is_left = False
        is_right = False
      elif not self.on_free_tile:
        # 昇降モードに入っていない平地では、上下キーで横歩きが止まらないようにする
        is_up = False
        is_down = False

      new_direction = self.direction
      is_input = False

      if is_up:
        new_direction = "up"
        is_input = True
      elif is_down:
        new_direction = "down"
        is_input = True
      elif is_left:
        new_direction = "left"
        is_input = True
      elif is_right:
        new_direction = "right"
        is_input = True

      if is_input:
        # 止まっている状態から歩き始めた最初の1歩目で発音
        if not self.was_moving:
          try:
            pyxel.play(0, 0)
          except Exception:
            pass
        self.moving = True
        self.skip_idle = False
        if new_direction != self.direction:
          self.direction = new_direction
          self.frame_x = 0
          self.frame_y = 0
          self.anim_timer = 0
          # ハシゴ昇降中に上下の向きが変わったら、横位置のズレを基準位置にリセット
          if self.climbing:
            self.x = self.get_stair_center_x()
      else:
        self.moving = False

      if self.was_moving and not self.moving:
        self.frame_x = 0
        self.frame_y = 0
        self.anim_timer = 0
        self.idle_step_count = 0

      # --- 2. キー入力による移動 ---
      if self.moving:
        self.anim_timer += 1
        if self.anim_timer >= self.anim_speed:
          self.anim_timer = 0
          anim_idx = self.get_anim_index()

          dx, dy = 0, 0
          if self.direction == "up" and (self.climbing or self.on_free_tile):
            dy = -self.up_main[anim_idx]
            dx = self.up_sub[anim_idx]   # ← はしご昇降中も UP-S の横揺れを適用
          elif self.direction == "down" and (self.climbing or self.on_free_tile):
            dy = self.down_main[anim_idx]
            dx = self.down_sub[anim_idx] # ← はしご昇降中も DN-S の横揺れを適用
          elif self.direction == "left" and not self.climbing:
            dx = -self.left_main[anim_idx]
            dy = self.left_sub[anim_idx]
          elif self.direction == "right" and not self.climbing:
            dx = self.right_main[anim_idx]
            dy = self.right_sub[anim_idx]

          # X方向の移動と壁判定（※はしご昇降中の横揺れは途中階の床に引っかからないよう許可）
          step_x = 1 if dx > 0 else -1
          for _ in range(abs(dx)):
            if self.climbing or not self.check_tile_collision(self.x + step_x, self.y, self.SOLID_TILES):
              self.x += step_x
            else:
              break

          # Y方向の移動と床・天井判定
          step_y = 1 if dy > 0 else -1
          for _ in range(abs(dy)):
            if self.climbing:
              # ① 上に登っているとき：はしごを登りきって上の床に乗ったら、床の2px上にピタッと揃えて停止＆ロック
              if step_y < 0:
                x1, _, x2, y2 = self.get_hitbox(self.x, self.y)
                check_y = y2 + 3
                foot_hits_solid = (
                    self.get_tile_at(x1, check_y) in self.SOLID_TILES
                    or self.get_tile_at(x2, check_y) in self.SOLID_TILES
                    or self.get_tile_at((x1 + x2) // 2, check_y) in self.SOLID_TILES
                )
                body_still_stair = self.check_tile_collision(self.x, self.y, self.STAIR_TILES)
                if not body_still_stair and foot_hits_solid:
                  # 床タイルの天面(8pxの倍数)を割り出し、その2px上にキャラの足元(self.y + self.height)をピタッと合わせる
                  floor_top_y = (int(check_y) // 8) * 8
                  self.y = floor_top_y - self.height - 1
                  self.climbing = False
                  self.lock_stair_up = True
                  self.stair_top_hold = True
                  self.moving = False
                  break

              # ② 下に降りているとき：すでにハシゴ本体に入っている状態で、足元2px下に床または自由移動タイルが現れたら着地＆解除
              elif step_y > 0:
                # 自分の体（ヒットボックス）が実際にハシゴ本体に触れているか（出発地点の床を通過中ならFalse）
                body_in_stair = self.check_tile_collision(self.x, self.y, self.STAIR_TILES)
                if body_in_stair:
                  x1, _, x2, y2 = self.get_hitbox(self.x, self.y)
                  check_y = y2 + 2
                  foot_hits_solid = (
                      self.get_tile_at(x1, check_y) in self.SOLID_TILES
                      or self.get_tile_at(x2, check_y) in self.SOLID_TILES
                      or self.get_tile_at((x1 + x2) // 2, check_y) in self.SOLID_TILES
                  )
                  foot_hits_stair = (
                      self.get_tile_at(x1, check_y) in self.STAIR_TILES
                      or self.get_tile_at(x2, check_y) in self.STAIR_TILES
                      or self.get_tile_at((x1 + x2) // 2, check_y) in self.STAIR_TILES
                  )
                  foot_hits_free = (
                      self.get_tile_at(x1, check_y) in self.FREE_MOVE_TILES
                      or self.get_tile_at(x2, check_y) in self.FREE_MOVE_TILES
                      or self.get_tile_at((x1 + x2) // 2, check_y) in self.FREE_MOVE_TILES
                  )
                  if (foot_hits_solid or foot_hits_free) and not foot_hits_stair:
                    # 自由移動ブロックへ降りた場合は、足元がしっかり接地する高さ(2px下)まで降ろしてから解除する
                    if foot_hits_free and not foot_hits_solid:
                      self.y += 2
                    self.climbing = False
                    self.lock_stair_dn = True
                    if foot_hits_solid:
                      self.moving = False
                    break

              self.y += step_y
            else:
              if not self.check_tile_collision(self.x, self.y + step_y, self.SOLID_TILES):
                # 自由移動ブロック内にいるとき：足元が自由移動ブロックの上下端から2px以上はみ出さないように制限
                if self.on_free_tile and not self.on_stair:
                  nx1, _, nx2, ny2 = self.get_hitbox(self.x, self.y + step_y)
                  foot_center_x = (nx1 + nx2) // 2

                  if step_y < 0:
                    # 上移動：足元の2px上（ny2 - 2）がまだ自由移動ブロック内にあるかチェック（上端から2px手前で停止）
                    still_in_free = (
                        self.get_tile_at(foot_center_x, ny2 - 2) in self.FREE_MOVE_TILES
                        or self.get_tile_at(nx1 + 2, ny2 - 2) in self.FREE_MOVE_TILES
                        or self.get_tile_at(nx2 - 2, ny2 - 2) in self.FREE_MOVE_TILES
                    )
                    if not still_in_free:
                      self.moving = False
                      self.lock_free_up = True  # 上端に到達したら別キーが押されるまでロック
                      break

                  elif step_y > 0:
                    # 下移動：足元（ny2 + 2）がまだ自由移動ブロック内にあるかチェック（下端から2px手前で停止）
                    still_in_free = (
                        self.get_tile_at(foot_center_x, ny2 + 2) in self.FREE_MOVE_TILES
                        or self.get_tile_at(nx1 + 2, ny2 + 2) in self.FREE_MOVE_TILES
                        or self.get_tile_at(nx2 - 2, ny2 + 2) in self.FREE_MOVE_TILES
                    )
                    if not still_in_free:
                      self.moving = False
                      self.lock_stair_dn = False  # 下端に到達したらハシゴ降りきりロックも解除し、左右へスライド移動できるようにする
                      # 真下にハシゴがある場合はロックせず、そのままハシゴ降りへ移行できるようにする
                      if not self.on_stair:
                        self.lock_free_dn = True
                      break

                self.y += step_y
              else:
                self.moving = False
                if step_y < 0:
                  self.lock_free_up = True
                elif step_y > 0:
                  self.lock_free_dn = True
                break

          self.frame_x = (self.frame_x + 1) % 3
          if self.frame_x == 0:
            # 1歩ごと（3コマに1回）に効果音 SOUND(0) をチャンネル0で再生
            try:
              pyxel.play(0, 0)
            except Exception:
              pass

            self.frame_y = 0 if self.frame_y == 1 else 1
            # アニメーションが1周（6コマ完了して0コマ目に戻った）したら横位置を基準位置に補正
            if self.frame_y == 0 and self.climbing:
              self.x = self.get_stair_center_x()
      else:
        # 停止中のアニメーション
        if self.skip_idle:
          self.frame_x = 2
          self.frame_y = 1
        else:
          current_idle_speed = (
              4 if self.direction in ["left", "right"] else self.anim_speed
          )
          if self.idle_step_count < 6:
            self.anim_timer += 1
            if self.anim_timer >= current_idle_speed:
              self.anim_timer = 0
              self.frame_x += 1
              if self.frame_x >= 3:
                self.frame_x = 0
                if self.frame_y == 0:
                  self.frame_y = 1
                else:
                  self.frame_x = 2
                  self.frame_y = 1
              self.idle_step_count += 1
          else:
            self.frame_x = 2
            self.frame_y = 1

      # --- 3. 重力処理（階段・自由移動タイルに触れていないときのみ落下） ---
      sx1, sy1, sx2, sy2 = self.get_hitbox(self.x, self.y)
      self.on_stair = False
      check_y_list = list(range(int(sy1), int(sy2) + 17, 2))
      for check_y in check_y_list:
        for check_x in range(int(sx1) + 4, int(sx2) - 3, 2):
          if self.get_tile_at(check_x, check_y) in self.STAIR_TILES:
            self.on_stair = True
            break
        if self.on_stair:
          break
      self.on_free_tile = self.check_tile_collision(self.x, self.y, self.FREE_MOVE_TILES)
      if not self.on_stair:
        self.climbing = False

      # 左右に動き出したら、登りきり高さキープを解除
      if is_left or is_right:
        self.stair_top_hold = False

      if self.climbing or self.on_free_tile or self.stair_top_hold:
        self.vy = 0.0
        self.on_ground = True
      else:
        # 階段から抜けた直後などに床や天井に埋まっていたら、近い方向（上または下）へ最大24pxまで押し出して救出する
        if self.check_tile_collision(self.x, self.y, self.SOLID_TILES):
          up_dist = None
          for lift in range(1, 25):
            if not self.check_tile_collision(self.x, self.y - lift, self.SOLID_TILES):
              up_dist = lift
              break
          down_dist = None
          for push_down in range(1, 25):
            if not self.check_tile_collision(self.x, self.y + push_down, self.SOLID_TILES):
              down_dist = push_down
              break
          if up_dist is not None and (down_dist is None or up_dist <= down_dist):
            self.y -= up_dist
          elif down_dist is not None:
            self.y += down_dist

        self.vy = min(self.vy + self.gravity, self.max_fall_speed)
        fall_pixels = int(self.vy)
        self.on_ground = False

        for _ in range(fall_pixels):
          if self.y + 2 > 208 - self.height or self.check_tile_collision(self.x, self.y + 2, self.SOLID_TILES):
            self.vy = 0.0
            self.on_ground = True
            break
          else:
            self.y += 1

    # 画面外に出ないように制限
    self.x = max(0, min(self.x, 208 - self.width))
    self.y = max(0, min(self.y, 208 - self.height))

  def draw(self):
    # 画面クリア（色番号 1: 暗い青紫）
    pyxel.cls(1)

    # タイルマップ（Tilemap 0）を画面全体に描画
    pyxel.bltm(0, 0, 0, 0, 0, 208, 208)

    # --- 状態に応じた描画 ---
    if self.state == "WARP_OUT":
      if 0 <= self.dron_frame <= self.max_dron_frame:
        dron_idx = int(self.dron_frame)
        u, v = self.get_effect_uv(dron_idx)
        pyxel.blt(int(self.x), int(self.y), 1, u, v, self.width, self.height, 0)

      if self.smoke_started:
        smoke_progress = int(self.smoke_frame)
        if smoke_progress >= 4:
          interval = 3 if smoke_progress < 8 else 2
          dron_idx = min(int(self.dron_frame), self.max_dron_frame)
          du, dv = self.get_effect_uv(dron_idx)
          img1 = pyxel.image(1)

          for dy in range(self.height):
            for dx in range(self.width):
              # ドロン画像側のピクセルが透明色(0)でない部分だけディザリングを適用
              if img1.pget(du + dx, dv + dy) != 0:
                px = int(self.x) + dx
                py = int(self.y) + dy
                if (px + py + pyxel.frame_count) % interval == 0:
                  pyxel.pset(px, py, 1)

      if self.smoke_started and (0 <= self.smoke_frame <= self.max_smoke_frame):
        smoke_idx = int(self.smoke_frame)
        u, v = self.get_smoke_uv(smoke_idx)
        pyxel.blt(int(self.x), int(self.y), 1, u, v, self.width, self.height, 0)

    elif self.state == "WARP_IN":
      if 0 <= self.dron_frame <= self.max_dron_frame:
        dron_idx = int(self.dron_frame)
        u, v = self.get_effect_uv(dron_idx)
        pyxel.blt(int(self.x), int(self.y), 1, u, v, self.width, self.height, 0)

      if 0 <= self.smoke_frame <= self.max_smoke_frame:
        smoke_idx = int(self.smoke_frame)
        u, v = self.get_smoke_uv(smoke_idx)
        pyxel.blt(int(self.x), int(self.y), 1, u, v, self.width, self.height, 0)

    # --- 通常時（WARP_OUT および WARP_IN の間はプレイヤーを描画しないように分離） ---
    elif self.state == "NORMAL":
      draw_w = -self.width if self.direction == "left" else self.width

      # ジャンプ中、またはデバッグのジャンプ調整モード中は (0, 128) の14コマシートを描画
      if (self.is_jumping and not self.debug_mode) or (self.debug_mode and self.debug_jump_mode):
        if self.jump_frame < 8:
          u = (self.jump_frame % 8) * self.width
          v = 128
        else:
          u = ((self.jump_frame - 8) % 8) * self.width
          v = 160
      else:
        u_base = 0 if (self.moving or self.debug_mode) else 96
        if self.direction == "down":
          v_base = 0
        elif self.direction == "up":
          v_base = 64
        elif self.direction == "left":
          v_base = 192
        elif self.direction == "right":
          v_base = 192

        u = u_base + (self.frame_x * self.width)
        v = v_base + (self.frame_y * self.height)

      pyxel.blt(
          int(self.x),
          int(self.y),
          0,
          u,
          v,
          draw_w,
          self.height,
          0,
      )

    # --- 調整モードが有効（True）のときだけ、画面右上に移動量テーブルを表示 ---
    if self.debug_mode:
      if self.debug_jump_mode:
        # 【ジャンプ移動量テーブル表示（前半0〜6コマ / 後半7〜13コマの2段表示）】
        pyxel.text(50, 2,  "JX0-6:", 11)
        pyxel.text(50, 12, "JY0-6:", 11)
        pyxel.text(50, 22, f"FRAME: {self.jump_frame:2d} / 13", 10)
        pyxel.text(50, 32, "JX7-D:", 11)
        pyxel.text(50, 42, "JY7-D:", 11)

        for col in range(7):
          x_pos = 78 + col * 16
          # 前半 (0〜6)
          col_top = 8 if self.jump_frame == col else 7
          pyxel.text(x_pos, 2,  f"{self.jump_dx[col]:>2}", col_top)
          pyxel.text(x_pos, 12, f"{self.jump_dy[col]:>2}", col_top)
          # 後半 (7〜13)
          idx_btm = col + 7
          col_btm = 8 if self.jump_frame == idx_btm else 7
          pyxel.text(x_pos, 32, f"{self.jump_dx[idx_btm]:>2}", col_btm)
          pyxel.text(x_pos, 42, f"{self.jump_dy[idx_btm]:>2}", col_btm)
      else:
        # 【通常歩行移動量テーブル表示】
        anim_idx = self.get_anim_index()

        display_tables = [
            ("UP-M:", self.up_main, "up"),
            ("UP-S:", self.up_sub, "up"),
            ("DN-M:", self.down_main, "down"),
            ("DN-S:", self.down_sub, "down"),
            ("LT-M:", self.left_main, "left"),
            ("LT-S:", self.left_sub, "left"),
            ("RT-M:", self.right_main, "right"),
            ("RT-S:", self.right_sub, "right"),
        ]

        start_y = 2
        for label, table, dir_name in display_tables:
          is_active_dir = self.direction == dir_name
          row_col = 8 if is_active_dir else 7

          pyxel.text(50, start_y, label, row_col)

          x_offset = 85
          for i in range(6):
            num_col = 8 if (is_active_dir and i == anim_idx) else 7
            pyxel.text(x_offset, start_y, str(table[i]), num_col)
            x_offset += 8

          pyxel.text(x_offset, start_y, "]", row_col)
          start_y += 10

      # --- パレット書き出しボタン (EXP PAL) ---
      btn_x, btn_y, btn_w, btn_h = 85, 84, 40, 10
      is_hover = (btn_x <= pyxel.mouse_x <= btn_x + btn_w) and (
          btn_y <= pyxel.mouse_y <= btn_y + btn_h
      )
      btn_bg = 11 if is_hover else 1
      pyxel.rect(btn_x, btn_y, btn_w, btn_h, btn_bg)
      pyxel.rectb(btn_x, btn_y, btn_w, btn_h, 7)
      pyxel.text(btn_x + 6, btn_y + 2, "EXP PAL", 7)

      # --- ★追加：ジャンプ／歩行テーブル切り替えボタン (JMP TBL / WLK TBL) ---
      jbtn_x, jbtn_y, jbtn_w, jbtn_h = 128, 84, 44, 10
      is_jhover = (jbtn_x <= pyxel.mouse_x <= jbtn_x + jbtn_w) and (
          jbtn_y <= pyxel.mouse_y <= jbtn_y + jbtn_h
      )
      jbtn_bg = 10 if self.debug_jump_mode else (11 if is_jhover else 1)
      jbtn_txt_col = 0 if self.debug_jump_mode else 7
      jbtn_label = "WLK TBL" if self.debug_jump_mode else "JMP TBL"
      pyxel.rect(jbtn_x, jbtn_y, jbtn_w, jbtn_h, jbtn_bg)
      pyxel.rectb(jbtn_x, jbtn_y, jbtn_w, jbtn_h, 7)
      pyxel.text(jbtn_x + 8, jbtn_y + 2, jbtn_label, jbtn_txt_col)

      # --- ★追加：移動テーブルコードコピーボタン (CPY TBL) ---
      cbtn_x, cbtn_y, cbtn_w, cbtn_h = 175, 84, 32, 10
      is_chover = (cbtn_x <= pyxel.mouse_x <= cbtn_x + cbtn_w) and (
          cbtn_y <= pyxel.mouse_y <= cbtn_y + cbtn_h
      )
      cbtn_bg = 11 if is_chover else 1
      pyxel.rect(cbtn_x, cbtn_y, cbtn_w, cbtn_h, cbtn_bg)
      pyxel.rectb(cbtn_x, cbtn_y, cbtn_w, cbtn_h, 7)
      pyxel.text(cbtn_x + 3, cbtn_y + 2, "CPY TBL", 7)

      # 書き出し・コピー完了メッセージ
      if self.export_msg_timer > 0:
        pyxel.text(85, 97, "SAVED .gpl!", 11)
      if self.copy_msg_timer > 0:
        pyxel.text(140, 97, "COPIED TBL!", 10)

      # --- ★ここから追加：足元のタイルID・タイル絵柄プレビューと当たり判定枠の可視化 ---
      x1, y1, x2, y2 = self.get_hitbox(self.x, self.y)
      # 当たり判定の枠を赤い四角で表示
      pyxel.rectb(int(x1), int(y1), int(x2 - x1 + 1), int(y2 - y1 + 1), 8)
      # 足元中央の2px下にあるタイルIDを取得して画面左上に表示
      foot_tile = self.get_tile_at((x1 + x2) // 2, y2 + 2)
      pyxel.text(2, 2, f"FOOT:{foot_tile}", 10)
      # FOOT表示のすぐ下に、いま踏んでいるタイルパターンをプレビュー描画
      fu, fv = foot_tile
      pyxel.blt(3, 10, 2, fu * 8, fv * 8, 8, 8, 0)
      pyxel.rectb(2, 9, 10, 10, 10)

      # --- ★ここから追加：はしご（STAIR_TILES）登録タイルのプレビュー表示 ---
      pyxel.text(2, 22, "STAIRS:", 11)
      # 重複を除いて順番を保ったタイル一覧を作成
      unique_stairs = list(dict.fromkeys(self.STAIR_TILES))
      for idx, (u_idx, v_idx) in enumerate(unique_stairs):
        preview_x = 3 + (idx % 4) * 10   # 横に最大4個ずつ、10px間隔で並べる（右側のテーブルと重ならない幅）
        preview_y = 30 + (idx // 4) * 10 # 4個を超えたら次の行へ折り返す
        # タイル画像の該当箇所 (Bank 2) を 8x8 で描画
        pyxel.blt(preview_x, preview_y, 2, u_idx * 8, v_idx * 8, 8, 8, 0)
        # 見やすいように枠線を描画
        pyxel.rectb(preview_x - 1, preview_y - 1, 10, 10, 7)

      # --- ★追加：自由移動（FREE_MOVE_TILES）登録タイルのプレビュー表示 ---
      pyxel.text(2, 54, "FREE:", 10)
      unique_free = list(dict.fromkeys(self.FREE_MOVE_TILES))
      for idx, (u_idx, v_idx) in enumerate(unique_free):
        preview_x = 3 + (idx % 4) * 10
        preview_y = 62 + (idx // 4) * 10
        pyxel.blt(preview_x, preview_y, 2, u_idx * 8, v_idx * 8, 8, 8, 0)
        pyxel.rectb(preview_x - 1, preview_y - 1, 10, 10, 7)

      # --- ★追加：クリックした場所のタイルIDとプレビュー表示 ---
      pyxel.text(2, 76, f"CLK:{self.clicked_tile}", 12)
      cu, cv = self.clicked_tile
      pyxel.blt(3, 84, 2, cu * 8, cv * 8, 8, 8, 0)
      pyxel.rectb(2, 83, 10, 10, 12)

      # マップ上のクリックしたマス目にも水色の枠線を表示
      if self.clicked_pos is not None:
        ctx, cty = self.clicked_pos
        pyxel.rectb(ctx * 8, cty * 8, 8, 8, 12)

      # --- ★追加：ハシゴ下り検知エリアと内部状態フラグの可視化 ---
      cx1, cy1, cx2, cy2 = self.get_hitbox(self.x, self.y)
      # 下キーでハシゴを探している範囲（足元1px〜16px下、横幅cx1+2〜cx2-1）を黄緑色の枠(色11)で表示
      scan_x = int(cx1) + 2
      scan_y = int(cy2) + 1
      scan_w = int(cx2 - 1) - scan_x + 1
      scan_h = 16
      pyxel.rectb(scan_x, scan_y, scan_w, scan_h, 11)

      # 左下（または左上の空きスペース）に現在の判定フラグをリアルタイム表示
      flag_y = 100
      pyxel.text(2, flag_y,      f"STAIR:{int(self.on_stair)} CLIMB:{int(self.climbing)}", 11)
      pyxel.text(2, flag_y + 8,  f"FREE :{int(self.on_free_tile)}", 10)
      pyxel.text(2, flag_y + 16, f"LK_SU:{int(self.lock_stair_up)} SD:{int(self.lock_stair_dn)}", 8)
      pyxel.text(2, flag_y + 24, f"LK_FU:{int(self.lock_free_up)} FD:{int(self.lock_free_dn)}", 8)

App()