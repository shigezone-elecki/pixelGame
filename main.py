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
    # パレット書き出し完了メッセージの表示タイマー  <-- ★ここを追加
    self.export_msg_timer = 0

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
      pyxel.image(0).load(0, 128, "karakusa_32_L.png")
      pyxel.image(0).load(0, 192, "karakusa_32_R.png")

      # Bank 0: 各方向の停止・アイドルグラフィック（右側：x=96）
      pyxel.image(0).load(96, 0, "karakusa_32_Fstp.png")
      pyxel.image(0).load(96, 64, "karakusa_32_Bstp.png")
      pyxel.image(0).load(96, 128, "karakusa_32_Lstp.png")
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

    # はしご（階段）のタイル定義
    self.STAIR_TILES = [
       (12, 1), (15, 1), (13, 1), (14, 1),(15, 1),(10, 1), (9, 2), (11, 1)
    ]

    # 重力設定
    self.vy = 0.0          # 落下速度
    self.gravity = 0.4     # 重力の強さ
    self.max_fall_speed = 6.0  # 最大落下速度
    self.on_ground = False # 接地フラグ
    self.on_stair = False  # 階段接触フラグ

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
      import js
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
    # 32x32画像のうち、左右8px・上8pxを削り、下端を1px広げることで床の1px上に着地させる
    return (x + 8, y + 8, x + self.width - 9, y + self.height)

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

  def update(self):
    # Qキーで終了
    if pyxel.btnp(pyxel.KEY_Q):
      pyxel.quit()

    # ★ここを追加（メッセージ表示タイマーを減らす）
    if self.export_msg_timer > 0:
      self.export_msg_timer -= 1

    # --- セレクトボタン（押し始め）で調整モードの表示・非表示をトグル ---
    if (
        pyxel.btnp(pyxel.GAMEPAD1_BUTTON_BACK)
        or pyxel.btnp(pyxel.KEY_TAB)
        or pyxel.btnp(pyxel.KEY_BACKSPACE)
    ):
      self.debug_mode = not self.debug_mode
      pyxel.mouse(self.debug_mode)  # 調整モード中だけカーソル表示

      if self.debug_mode:
        pyxel.stop()  # 調整モードに入ったらBGM停止
      else:
        pyxel.playm(0, loop=True)  # 調整モードを抜けたらBGM再開

    # --- 調整モード表示中のみマウス操作による数値調整を受け付ける ---
    if self.debug_mode:
      mx, my = pyxel.mouse_x, pyxel.mouse_y
      left_clicked = pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
      right_clicked = pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT)

      # ★ここを追加（パレット書き出しボタンのクリック判定）
      if left_clicked and (85 <= mx <= 133) and (84 <= my <= 94):
        self.export_palette_for_aseprite()

      # ★元の `if left_clicked or right_clicked:` を `elif` に変更
      elif left_clicked or right_clicked:
        delta = 1 if left_clicked else -1

      if left_clicked or right_clicked:
        delta = 1 if left_clicked else -1

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
        anim_idx = self.get_anim_index()
        # 現在のコマの移動量を適用して1コマ進める
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
        # 1コマ戻してから、そのコマの移動量を逆方向に引き戻す
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

      # 1. 現在「階段」に触れているか、または「足元1px下」に階段があるかチェック
      self.on_stair = (
          self.check_tile_collision(self.x, self.y, self.STAIR_TILES)
          or self.check_tile_collision(self.x, self.y + 1, self.STAIR_TILES)
      )

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

      # 階段にいないときは「上移動」の入力を無効化（空中浮遊防止）
      if not self.on_stair:
        is_up = False

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
        self.moving = True
        self.skip_idle = False
        if new_direction != self.direction:
          self.direction = new_direction
          self.frame_x = 0
          self.frame_y = 0
          self.anim_timer = 0
      else:
        self.moving = False

      if self.was_moving and not self.moving:
        self.frame_x = 0
        self.frame_y = 0
        self.anim_timer = 0
        self.idle_step_count = 0

      # --- 2. キー入力による移動（1pxずつ判定して壁めり込み防止） ---
      if self.moving:
        self.anim_timer += 1
        if self.anim_timer >= self.anim_speed:
          self.anim_timer = 0
          anim_idx = self.get_anim_index()

          dx, dy = 0, 0
          if self.direction == "up" and self.on_stair:
            dy = -self.up_main[anim_idx]
            dx = self.up_sub[anim_idx]
          elif self.direction == "down":
            # 階段のときだけ下移動の移動量テーブルを適用（平地では重力に任せる）
            if self.on_stair:
              dy = self.down_main[anim_idx]
              dx = self.down_sub[anim_idx]
          elif self.direction == "left":
            dx = -self.left_main[anim_idx]
            dy = self.left_sub[anim_idx]
          elif self.direction == "right":
            dx = self.right_main[anim_idx]
            dy = self.right_sub[anim_idx]

          # X方向の移動と壁判定（階段に触れている間は床・壁をすり抜ける）
          step_x = 1 if dx > 0 else -1
          for _ in range(abs(dx)):
            if self.on_stair or not self.check_tile_collision(self.x + step_x, self.y, self.SOLID_TILES):
              self.x += step_x
            else:
              break

          # Y方向の移動と床・天井判定（階段に触れている間は床をすり抜ける）
          step_y = 1 if dy > 0 else -1
          for _ in range(abs(dy)):
            if self.on_stair or not self.check_tile_collision(self.x, self.y + step_y, self.SOLID_TILES):
              self.y += step_y
            else:
              break

          self.frame_x = (self.frame_x + 1) % 3
          if self.frame_x == 0:
            self.frame_y = 0 if self.frame_y == 1 else 1
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

      # --- 3. 重力処理（階段に触れていないときのみ落下） ---
      # 移動後に改めて階段接触を再チェック
      self.on_stair = self.check_tile_collision(self.x, self.y, self.STAIR_TILES)

      if self.on_stair:
        self.vy = 0.0
        self.on_ground = False
      else:
        # 階段から抜けた直後などに足元が少しだけ床に埋まっていたら上に押し出す（最大8pxまで救済）
        if self.check_tile_collision(self.x, self.y, self.SOLID_TILES):
          for lift in range(1, 9):
            if not self.check_tile_collision(self.x, self.y - lift, self.SOLID_TILES):
              self.y -= lift
              break

        self.vy = min(self.vy + self.gravity, self.max_fall_speed)
        fall_pixels = int(self.vy)
        self.on_ground = False

        for _ in range(fall_pixels):
          # 1px下に床があるか、または画面最下部に到達したか
          if self.y + 1 > 208 - self.height or self.check_tile_collision(self.x, self.y + 1, self.SOLID_TILES):
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
      u_base = 0
      v_base = 0

      if self.moving or self.debug_mode:
        u_base = 0  # 歩行シートは左側 (x=0)
      else:
        u_base = 96  # 停止・アイドルシートは右側 (x=96)

      if self.direction == "down":
        v_base = 0
      elif self.direction == "up":
        v_base = 64
      elif self.direction == "left":
        v_base = 128
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
          self.width,
          self.height,
          0,
      )

    # --- 調整モードが有効（True）のときだけ、画面右上に移動量テーブルを表示 ---
    if self.debug_mode:
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

        # ラベルを描画
        pyxel.text(50, start_y, label, row_col)

        # 6コマ分の数字を 8px 間隔で描画（開始位置 x = 85）
        x_offset = 85
        for i in range(6):
          num_col = 8 if (is_active_dir and i == anim_idx) else 7
          pyxel.text(x_offset, start_y, str(table[i]), num_col)
          x_offset += 8

        pyxel.text(x_offset, start_y, "]", row_col)

        start_y += 10

      # --- ★ここから下を追加：パレット書き出しボタンの描画 ---
      btn_x, btn_y, btn_w, btn_h = 85, 84, 48, 10
      is_hover = (btn_x <= pyxel.mouse_x <= btn_x + btn_w) and (
          btn_y <= pyxel.mouse_y <= btn_y + btn_h
      )
      btn_bg = 11 if is_hover else 1
      pyxel.rect(btn_x, btn_y, btn_w, btn_h, btn_bg)
      pyxel.rectb(btn_x, btn_y, btn_w, btn_h, 7)
      pyxel.text(btn_x + 4, btn_y + 2, "EXP PAL", 7)

      # 書き出し完了メッセージ
      if self.export_msg_timer > 0:
        pyxel.text(85, 97, "SAVED .gpl!", 11)

      # --- ★ここから追加：足元のタイルIDと当たり判定枠の可視化 ---
      x1, y1, x2, y2 = self.get_hitbox(self.x, self.y)
      # 当たり判定の枠を赤い四角で表示
      pyxel.rectb(int(x1), int(y1), int(x2 - x1 + 1), int(y2 - y1 + 1), 8)
      # 足元中央の1px下にあるタイルIDを取得して画面左上に表示
      foot_tile = self.get_tile_at((x1 + x2) // 2, y2 + 1)
      pyxel.text(2, 2, f"FOOT:{foot_tile}", 10)


App()