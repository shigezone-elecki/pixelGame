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

    # --- ワープ（ドロン）用の状態管理 ---
    self.state = "NORMAL"  # "NORMAL", "WARP_OUT", "WARP_IN"
    self.effect_timer = 0
    self.dron_frame = 0  # ドロンアニメーションのコマ番 (0 〜 14)
    self.smoke_frame = 0  # ケムリアニメーションのコマ番
    self.max_dron_frame = 14  # 全15コマ（0始まり）

    # 【画像の読み込み】
    try:
      # Bank 0: 歩行・停止グラフィック
      pyxel.images[0].load(0, 0, "karakusa_32_F.png")
      pyxel.images[0].load(0, 64, "karakusa_32_B.png")
      pyxel.images[0].load(0, 128, "karakusa_32_L.png")
      pyxel.images[0].load(0, 192, "karakusa_32_R.png")
      pyxel.images[0].load(96, 0, "karakusa_32_Fstp.png")

      # Bank 1: エフェクト用（ドロン ＆ ケムリ）[cite: 7, 8, 9]
      pyxel.images[1].load(0, 0, "karakusa_32_DronF.png")
      pyxel.images[1].load(0, 32, "karakusa_32_Smoke.png")
    except Exception as e:
      print(f"画像ロードエラー: {e}")

    pyxel.run(self.update, self.draw)

  def update(self):
    # Qキーで終了
    if pyxel.btnp(pyxel.KEY_Q):
      pyxel.quit()

    # --- 1. 消えるときの演出 (WARP_OUT) ---
    if self.state == "WARP_OUT":
      self.effect_timer += 1
      if self.effect_timer >= 2:  # 速度調整
        self.effect_timer = 0
        self.dron_frame += 1

        # 後半の4コマ目（11〜14コマ目）に入ったら煙をスタートさせる
        if self.dron_frame >= 11:
          self.smoke_frame += 1

        # 最後まで行ったら新しい場所へワープし、現れる演出へ
        if self.dron_frame > self.max_dron_frame:
          self.x = random.randint(0, 256 - self.width)
          self.y = random.randint(0, 256 - self.height)

          self.state = "WARP_IN"
          self.dron_frame = self.max_dron_frame  # 最後のポーズから逆再生スタート
          self.smoke_frame = 0  # 現れるときは煙を最初から
          self.effect_timer = 0
      return

    # --- 2. 現れるときの演出 (WARP_IN) ---
    elif self.state == "WARP_IN":
      self.effect_timer += 1
      if self.effect_timer >= 2:
        self.effect_timer = 0
        self.dron_frame -= 1  # 逆再生
        self.smoke_frame += 1  # 煙進行

        # ドロンが最初に戻りきったら通常状態へ
        if self.dron_frame < 0:
          self.state = "NORMAL"
      return

    # --- 3. 通常時の処理（移動・ワープトリガー） ---
    is_warp = pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(
        pyxel.GAMEPAD1_BUTTON_A
    )
    if is_warp:
      self.state = "WARP_OUT"
      self.dron_frame = 0
      self.smoke_frame = 0
      self.effect_timer = 0
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

    # 画面外に出ないように制限（256x256基準）[cite: 7]
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

  def draw(self):
    # 画面クリア（色番号 1: 暗い青紫）[cite: 7]
    pyxel.cls(1)

    # --- 状態に応じた描画 ---
    if self.state == "WARP_OUT":
      # 1. キャラクタ（ドロンアニメーション正再生）
      u_dron = self.dron_frame * self.width
      pyxel.blt(int(self.x), int(self.y), 1, u_dron, 0, self.width, self.height, 0)

      # 2. 最後の4コマ（11〜14コマ目）のときだけ煙をオーバーラップ
      if self.dron_frame >= 11:
        u_smoke = self.smoke_frame * self.width
        pyxel.blt(
            int(self.x), int(self.y), 1, u_smoke, 32, self.width, self.height, 0
        )

    elif self.state == "WARP_IN":
      # 1. 現れた直後の前半（逆再生の14〜11コマ目）のときだけ煙をオーバーラップ
      if self.dron_frame >= 11:
        u_smoke = self.smoke_frame * self.width
        pyxel.blt(
            int(self.x), int(self.y), 1, u_smoke, 32, self.width, self.height, 0
        )

      # 2. キャラクタ（ドロンアニメーション逆再生）
      u_dron = self.dron_frame * self.width
      pyxel.blt(int(self.x), int(self.y), 1, u_dron, 0, self.width, self.height, 0)

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