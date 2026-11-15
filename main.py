import random
import pyxel


class App:

  def __init__(self):
    # 画面サイズを 256x256 の正方形に統一
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

    # --- ワープおよび独立アニメーション用の状態管理 ---
    self.state = "NORMAL"  # "NORMAL", "WARP_OUT", "WARP_IN", "TEST_DRON"

    # 独立したタイムライン用変数
    self.dron_frame = 0.0  # ドロン用フレーム (0 〜 12)
    self.dron_timer = 0  # ドロンのコマ送りタイマー

    self.smoke_frame = 0.0  # ケムリ用フレーム (0 〜 12)
    self.smoke_timer = 0  # ケムリのコマ送りタイマー
    self.smoke_started = False  # ケムリを遅延スタートさせるためのフラグ

    self.max_dron_frame = 12
    self.max_smoke_frame = 12

    # 【画像の読み込み】
    try:
      # Bank 0: 歩行・停止グラフィック
      pyxel.images[0].load(0, 0, "karakusa_32_F.png")
      pyxel.images[0].load(0, 64, "karakusa_32_B.png")
      pyxel.images[0].load(0, 128, "karakusa_32_L.png")
      pyxel.images[0].load(0, 192, "karakusa_32_R.png")
      pyxel.images[0].load(96, 0, "karakusa_32_Fstp.png")

      # Bank 1: エフェクト用（ドロン ＆ ケムリ）[cite: 7]
      pyxel.images[1].load(0, 0, "karakusa_32_DronF.png")
      pyxel.images[1].load(0, 32, "karakusa_32_Smoke.png")
    except Exception as e:
      print(f"画像ロードエラー: {e}")

    pyxel.run(self.update, self.draw)

  def update(self):
    # Qキーで終了
    if pyxel.btnp(pyxel.KEY_Q):
      pyxel.quit()

    # --- 【テスト用】ドロン単体再生モード（煙なし、フレーム番号表示付き） ---
    if self.state == "TEST_DRON":
      self.dron_timer += 1
      # 最後の3コマ（10, 11, 12コマ目）だけタメを長くする
      dron_speed = 15 if int(self.dron_frame) >= 10 else 4

      if self.dron_timer >= dron_speed:
        self.dron_timer = 0
        self.dron_frame += 1

        # 12コマ目を超えたら（13になったら）テスト終了してリセット
        if self.dron_frame > self.max_dron_frame:
          self.state = "NORMAL"
      return

    # --- 1. 消えるときの演出 (WARP_OUT) ---
    if self.state == "WARP_OUT":
      self.dron_timer += 1
      dron_speed = 15 if int(self.dron_frame) >= 10 else 4

      if self.dron_timer >= dron_speed:
        self.dron_timer = 0
        self.dron_frame += 1
        if self.dron_frame >= 4:
          self.smoke_started = True

      if self.smoke_started:
        self.smoke_timer += 1
        if self.smoke_timer >= 3:
          self.smoke_timer = 0
          self.smoke_frame += 1

      if (
          self.dron_frame > self.max_dron_frame
          and self.smoke_frame > self.max_smoke_frame
      ):
        self.x = random.randint(0, 256 - self.width)
        self.y = random.randint(0, 256 - self.height)

        self.state = "WARP_IN"
        self.dron_frame = float(self.max_dron_frame)
        self.dron_timer = 0
        self.smoke_frame = 0.0
        self.smoke_timer = 0
        self.smoke_started = True
      return

    # --- 2. 現れるときの演出 (WARP_IN) ---
    elif self.state == "WARP_IN":
      self.dron_timer += 1
      dron_speed = 15 if int(self.dron_frame) >= 10 else 4

      if self.dron_timer >= dron_speed:
        self.dron_timer = 0
        self.dron_frame -= 1

      self.smoke_timer += 1
      if self.smoke_timer >= 3:
        self.smoke_timer = 0
        self.smoke_frame += 1

      if self.dron_frame < 0 and self.smoke_frame > self.max_smoke_frame:
        self.state = "NORMAL"
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
      return

    # 【テスト用トリガー】Xキー または ゲームパッドのX/Bボタンでドロン単体テスト
    is_test = (
        pyxel.btnp(pyxel.KEY_X)
        or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X)
        or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)
    )
    if is_test:
      self.state = "TEST_DRON"
      self.dron_frame = 0.0
      self.dron_timer = 0
      return

    self.was_moving = self.moving
    self.moving = False

    # キーボード ＋ バーチャルパッド（DPAD）の入力を両方受け付ける[cite: 7]
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

    self.x = max(0, min(self.x, 256 - self.width))
    self.y = max(0, min(self.y, 256 - self.height))

    if self.was_moving and not self.moving:
      self.frame_x = 0
      self.frame_y = 0
      self.anim_timer = 0
      self.idle_step_count = 0

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

  def draw(self):
    # 画面クリア（色番号 1: 暗い青紫）[cite: 7]
    pyxel.cls(1)

    # --- 状態に応じた描画 ---
    if self.state == "TEST_DRON":
      # テスト用：ドロンアニメーション単体のみ描画
      if 0 <= self.dron_frame <= self.max_dron_frame:
        dron_idx = int(self.dron_frame)
        u_dron = dron_idx * self.width
        pyxel.blt(int(self.x), int(self.y), 1, u_dron, 0, self.width, self.height, 0)

        # 画面上に現在のフレーム番号（0〜12）をテキスト表示して確認できるようにする
        pyxel.text(
            int(self.x),
            int(self.y) - 10,
            f"FRAME: {dron_idx}",
            7,  # 7: 白文字
        )

    elif self.state == "WARP_OUT":
      if 0 <= self.dron_frame <= self.max_dron_frame:
        dron_idx = int(self.dron_frame)
        u_dron = dron_idx * self.width
        pyxel.blt(int(self.x), int(self.y), 1, u_dron, 0, self.width, self.height, 0)

      if self.smoke_started and (0 <= self.smoke_frame <= self.max_smoke_frame):
        smoke_idx = int(self.smoke_frame)
        u_smoke = smoke_idx * self.width
        pyxel.blt(
            int(self.x), int(self.y), 1, u_smoke, 32, self.width, self.height, 0
        )

    elif self.state == "WARP_IN":
      if 0 <= self.smoke_frame <= self.max_smoke_frame:
        smoke_idx = int(self.smoke_frame)
        u_smoke = smoke_idx * self.width
        pyxel.blt(
            int(self.x), int(self.y), 1, u_smoke, 32, self.width, self.height, 0
        )

      if 0 <= self.dron_frame <= self.max_dron_frame:
        dron_idx = int(self.dron_frame)
        u_dron = dron_idx * self.width
        pyxel.blt(
            int(self.x), int(self.y), 1, u_dron, 0, self.width, self.height, 0
        )

    else:
      # 通常時のプレイヤー描画
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