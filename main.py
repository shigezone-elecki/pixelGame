import pyxel


class App:

  def __init__(self):
    # 画面サイズ 256x256 で初期化
    pyxel.init(256, 256, title="Pixel Game - Pyxel", fps=60)

    # プレイヤーの初期状態
    self.x = 120
    self.y = 100
    self.width = 32
    self.height = 32

    self.direction = "down"  # "down", "up", "left", "right"
    self.moving = False
    self.was_moving = False

    self.frame_x = 0
    self.frame_y = 0
    self.anim_timer = 0
    self.anim_speed = 5
    self.idle_step_count = 0

    # 【画像の読み込み】
    # すべてイメージバンク 0 の中に、位置（x, y）をずらして並べてロードします！
    # これによりイメージバンクの範囲外エラーを防げます。
    try:
      pyxel.images[0].load(0, 0, "player_sheet_F.png")  # 下向き歩行: (0, 0)
      pyxel.images[0].load(0, 64, "player_sheet_B.png")  # 上向き歩行: (0, 64)
      pyxel.images[0].load(0, 128, "player_sheet_L.png")  # 左向き歩行: (0, 128)
      pyxel.images[0].load(0, 192, "player_sheet_R.png")  # 右向き歩行: (0, 192)
      pyxel.images[0].load(96, 0, "player_sheet_Fstp.png")  # 停止用: (96, 0)
    except Exception as e:
      print(f"画像ロードエラー: {e}")

    pyxel.run(self.update, self.draw)

def update(self):
    self.was_moving = self.moving
    self.moving = False

    # キーボード入力のフラグ
    is_up = pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W)
    is_down = pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S)
    is_left = pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A)
    is_right = pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D)

    # スマホのタッチ（またはマウスの左クリック）操作の追加
    if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
      mx, my = pyxel.mouse_x, pyxel.mouse_y
      
      # 画面を十字に分割して、タッチされた場所で方向を決定する例
      # （画面サイズ 256x256 の場合、中心を基準にするなど）
      # ここでは「キャラクターから見てどちらの方向か」または「画面の上下左右の端か」を判定します
      
      # 方法：キャラクターとタッチ位置の差分を見る場合
      dx = mx - (self.x + self.width / 2)
      dy = my - (self.y + self.height / 2)
      
      # タッチ位置がキャラクターから少し離れている場合のみ移動
      if abs(dx) > 4 or abs(dy) > 4:
        if abs(dx) > abs(dy):
          if dx < 0:
            is_left = True
          else:
            is_right = True
        else:
          if dy < 0:
            is_up = True
          else:
            is_down = True

    # 決定したフラグに基づいて実際に座標と向きを更新
    if is_up:
      self.y -= 0.8
      self.direction = "up"
      self.moving = True
    elif is_down:
      self.y += 0.8
      self.direction = "down"
      self.moving = True
    elif is_left:
      self.x -= 1
      self.direction = "left"
      self.moving = True
    elif is_right:
      self.x += 1
      self.direction = "right"
      self.moving = True

    # 停止状態に切り替わった瞬間のリセット
    if self.was_moving and not self.moving:
      self.frame_x = 0
      self.frame_y = 0
      self.anim_timer = 0
      self.idle_step_count = 0

    # アニメーションの処理
    if self.moving:
      # 【移動中】歩行アニメーションのループ
      self.anim_timer += 1
      if self.anim_timer >= self.anim_speed:
        self.anim_timer = 0
        self.frame_x = (self.frame_x + 1) % 3
        if self.frame_x == 0:
          self.frame_y = 0 if self.frame_y == 1 else 1
    else:
      # 【停止中】全6コマを1回だけ再生して最後のコマで止まる
      if self.idle_step_count < 6:
        self.anim_timer += 1
        if self.anim_timer >= self.anim_speed:
          self.anim_timer = 0
          self.frame_x += 1
          if self.frame_x >= 3:
            self.frame_x = 0
            self.frame_y = 0 if self.frame_y == 1 else 1
          self.idle_step_count += 1

          if self.idle_step_count >= 6:
            self.frame_x = 2
            self.frame_y = 1
      else:
        self.frame_x = 2
        self.frame_y = 1

    # Qキーで終了
    if pyxel.btnp(pyxel.KEY_Q):
      pyxel.quit()

  def draw(self):
    # 画面クリア（色番号 1: 暗い青紫）
    pyxel.cls(1)

    # 状態に応じて、イメージバンク0内の「切り出し開始位置（u_base, v_base）」を決める
    u_base = 0
    v_base = 0

    if self.moving:
      if self.direction == "down":
        u_base, v_base = 0, 0
      elif self.direction == "up":
        u_base, v_base = 0, 64
      elif self.direction == "left":
        u_base, v_base = 0, 128
      elif self.direction == "right":
        u_base, v_base = 0, 192
    else:
      # 停止時は共通の Fstp シートの配置場所（96, 0）を基準にする
      u_base, v_base = 96, 0

    # 基準位置 ＋ アニメーションのコマ位置（frame_x, frame_y）を足して切り出す
    u = u_base + (self.frame_x * self.width)
    v = v_base + (self.frame_y * self.height)

    # Pyxelの blt で描画（img=0 を使用。colkey=0 で黒背景を透明化）
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


App()