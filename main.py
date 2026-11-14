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

    # バーチャルパッドやキーボードの入力を受け取る
    is_up = pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W)
    is_down = pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S)
    is_left = pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A)
    is_right = pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D)

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

    # 画面外に出ないように制限
    self.x = max(0, min(self.x, 256 - self.width))
    self.y = max(0, min(self.y, 256 - self.height))

    # 停止状態に切り替わった瞬間のリセット
    if self.was_moving and not self.moving:
      self.frame_x = 0
      self.frame_y = 0
      self.anim_timer = 0
      self.idle_step_count = 0

    # アニメーションの処理
    if self.moving:
      self.anim_timer += 1
      if self.anim_timer >= self.anim_speed:
        self.anim_timer = 0
        self.frame_x = (self.frame_x + 1) % 3
        if self.frame_x == 0:
          self.frame_y = 0 if self.frame_y == 1 else 1
    else:
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

    # プレイヤーの描画
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
      u_base, v_base = 96, 0

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


App()