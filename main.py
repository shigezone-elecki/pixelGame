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
    self.state = "NORMAL"  # "NORMAL" (通常), "WARP_OUT" (消える演出), "WARP_IN" (現れる演出)
    self.effect_timer = 0
    self.dron_frame = 0  # ドロンアニメーションのコマ番
    self.smoke_frame = 0  # ケムリアニメーションのコマ番
    self.target_x = self.x
    self.target_y = self.y

    # 【画像の読み込み】
    try:
      # Bank 0: 歩行・停止グラフィック
      pyxel.images[0].load(0, 0, "karakusa_32_F.png")
      pyxel.images[0].load(0, 64, "karakusa_32_B.png")
      pyxel.images[0].load(0, 128, "karakusa_32_L.png")
      pyxel.images[0].load(0, 192, "karakusa_32_R.png")
      pyxel.images[0].load(96, 0, "karakusa_32_Fstp.png")

      # Bank 1: エフェクト用（ドロン ＆ ケムリ）
      pyxel.images[1].load(0, 0, "karakusa_32_DronF.png")
      pyxel.images[1].load(0, 32, "karakusa_32_Smoke.png")
    except Exception as e:
      print(f"画像ロードエラー: {e}")

    pyxel.run(self.update, self.draw)

  def update(self):
    # Qキーで終了
    if pyxel.btnp(pyxel.KEY_Q):
      pyxel.quit()

    # --- 1. ワープ（ドロン）中の処理 ---
    if self.state == "WARP_OUT":
      # 消えるときのドロンアニメーション進行
      self.effect_timer += 1
      if self.effect_timer >= 3:  # アニメーションの速度調整
        self.effect_timer = 0
        self.dron_frame += 1
        # 画像のコマ数に合わせて調整（仮に15コマとして、端に達したらワープ実行）
        if self.dron_frame >= 15:
          # ランダムな新しい座標へワープ先を決定
          self.x = random.randint(0, 256 - self.width)
          self.y = random.randint(0, 256 - self.height)
          # 次にケムリ出現演出へ移行
          self.state = "WARP_IN"
          self.smoke_frame = 0
          self.effect_timer = 0
      return

    elif self.state == "WARP_IN":
      # 現れるときのケムリアニメーション進行
      self.effect_timer += 1
      if self.effect_timer >= 3:
        self.effect_timer = 0
        self.smoke_frame += 1
        # ケムリのコマ数が終わったら通常状態に戻る（仮に15コマ）
        if self.smoke_frame >= 15:
          self.state = "NORMAL"
      return

    # --- 2. 通常時の処理（移動・ワープトリガー） ---
    # ワープのトリガー（スペースキー または ゲームパッドのAボタン）
    is_warp = pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(
        pyxel.GAMEPAD1_BUTTON_A
    )
    if is_warp:
      self.state = "WARP_OUT"
      self.dron_frame = 0
      self.effect_timer = 0
      return

    self.was_moving = self.moving
    self.moving = False

    # キーボード ＋ バーチャルパッド（DPAD）の入力を両方受け付ける
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

    # 画面外に出ないように制限（256x256基準）
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
    # 画面クリア（色番号 1: 暗い青紫）
    pyxel.cls(1)

    # --- 状態に応じた描画 ---
    if self.state == "WARP_OUT":
      # ドロンアニメーション（Image 1の y=0 から描画）
      u = self.dron_frame * self.width
      v = 0
      pyxel.blt(
          int(self.x),
          int(self.y),
          1,
          u,
          v,
          self.width,
          self.height,
          0,
      )

    elif self.state == "WARP_IN":
      # 現れた場所でのケムリアニメーション（Image 1の y=32 から描画）
      u = self.smoke_frame * self.width
      v = 32
      pyxel.blt(
          int(self.x),
          int(self.y),
          1,
          u,
          v,
          self.width,
          self.height,
          0,
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