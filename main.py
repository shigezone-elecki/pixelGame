import random
import pyxel


class App:

  def __init__(self):
    # 画面サイズを 208x208 に設定
    pyxel.init(208, 208, title="Pixel Game - Pyxel", fps=60)

    # プレイヤーの初期状態
    self.x = 80
    self.y = 80
    self.width = 32
    self.height = 32

    self.direction = "down"  # "down", "up", "left", "right"
    self.moving = False
    self.was_moving = False

    self.frame_x = 0
    self.frame_y = 0
    self.anim_timer = 0
    self.anim_speed = 6
    self.idle_step_count = 0

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

    # 【画像の読み込み】
    try:
      # Bank 0: 歩行グラフィック（左側：x=0）
      pyxel.images[0].load(0, 0, "karakusa_32_F.png")
      pyxel.images[0].load(0, 64, "karakusa_32_B.png")
      pyxel.images[0].load(0, 128, "karakusa_32_L.png")
      pyxel.images[0].load(0, 192, "karakusa_32_R.png")

      # Bank 0: 各方向の停止・アイドルグラフィック（右側：x=96）
      pyxel.images[0].load(96, 0, "karakusa_32_Fstp.png")
      pyxel.images[0].load(96, 64, "karakusa_32_Bstp.png")
      pyxel.images[0].load(96, 128, "karakusa_32_Lstp.png")
      pyxel.images[0].load(96, 192, "karakusa_32_Rstp.png")

      # Bank 1: エフェクト用（縦2段のスプライトシート）
      pyxel.images[1].load(0, 0, "karakusa_32_DronF.png")
      pyxel.images[1].load(0, 64, "karakusa_32_Smoke.png")
    except Exception as e:
      print(f"画像ロードエラー: {e}")

    pyxel.run(self.update, self.draw)

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

  def update(self):
    # Qキーで終了
    if pyxel.btnp(pyxel.KEY_Q):
      pyxel.quit()

    # --- 1. 消えるときの演出 (WARP_OUT) ---
    if self.state == "WARP_OUT":
      # ① ドロン！の進行（最後の3コマでタメる）
      self.dron_timer += 1
      dron_speed = 15 if int(self.dron_frame) >= 10 else 4

      if self.dron_timer >= dron_speed:
        self.dron_timer = 0
        if self.dron_frame <= self.max_dron_frame:
          self.dron_frame += 1

        # ドロンが「8コマ目」に到達したタイミングで煙の再生をスタート
        if int(self.dron_frame) >= 8:
          self.smoke_started = True

      # ② ケムリの進行
      if self.smoke_started:
        self.smoke_timer += 1
        if self.smoke_timer >= 5:
          self.smoke_timer = 0
          if self.smoke_frame <= self.max_smoke_frame:
            self.smoke_frame += 1

      # 両方のアニメーションが最後まで完了したらワープ先へ
      if (
          self.dron_frame > self.max_dron_frame
          and self.smoke_frame > self.max_smoke_frame
      ):
        max_x = max(0, 208 - self.width)
        max_y = max(0, 208 - self.height)
        self.x = random.randint(0, max_x)
        self.y = random.randint(0, max_y)

        # 現れる演出（WARP_IN）に移行
        self.state = "WARP_IN"
        self.dron_frame = float(self.max_dron_frame)
        self.dron_timer = 0
        self.smoke_frame = 0.0
        self.smoke_timer = 0
        self.smoke_started = True
      return

    # --- 2. 現れるときの演出 (WARP_IN) ---
    elif self.state == "WARP_IN":
      # ① ドロン逆再生（0コマ目まで来たらそこで止めて維持）
      self.dron_timer += 1
      if self.dron_timer >= 4:
        self.dron_timer = 0
        if self.dron_frame > 0:
          self.dron_frame -= 1

      # ② 煙の進行
      self.smoke_timer += 1
      if self.smoke_timer >= 5:
        self.smoke_timer = 0
        if self.smoke_frame <= self.max_smoke_frame:
          self.smoke_frame += 1

      # 煙が最後まで再生しきったら通常状態へ
      if self.smoke_frame > self.max_smoke_frame:
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

    if is_up:
      self.y -= 1
      self.direction = "up"
      self.moving = True
    elif is_down:
      self.y += 1
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

    self.x = max(0, min(self.x, 208 - self.width))
    self.y = max(0, min(self.y, 208 - self.height))

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
      # --- 停止中のアニメーション ---
      # 左右（left, right）のときだけアニメーションスピードを上げる（例: 通常6のところを 3 にする）
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

  def draw(self):
    # 画面クリア（色番号 1: 暗い青紫）
    pyxel.cls(1)

    # --- 状態に応じた描画 ---
    if self.state == "WARP_OUT":
      # ① ドロン！のキャラクターを描画
      if 0 <= self.dron_frame <= self.max_dron_frame:
        dron_idx = int(self.dron_frame)
        u, v = self.get_effect_uv(dron_idx)
        pyxel.blt(int(self.x), int(self.y), 1, u, v, self.width, self.height, 0)

      # ② 【ディザリング（網点）フェード効果】
      if self.smoke_started:
        smoke_progress = int(self.smoke_frame)
        if smoke_progress >= 4:
          interval = 3 if smoke_progress < 8 else 2
          for py in range(int(self.y), int(self.y) + self.height):
            for px in range(int(self.x), int(self.x) + self.width):
              if (px + py + pyxel.frame_count) % interval == 0:
                pyxel.pset(px, py, 1)

      # ③ ケムリ（上）を後に描画して被せる
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

    else:
      # 通常時のプレイヤー描画
      u_base = 0
      v_base = 0

      if self.moving:
        u_base = 0  # 歩行シートは左側 (x=0)
      else:
        u_base = 96  # 停止・アイドルシートは右側 (x=96)

      # 方向ごとの y 座標オフセットを設定
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


App()