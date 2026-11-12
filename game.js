const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

// プレイヤーの状態管理
const player = {
    x: 120,
    y: 100,
    width: 32,
    height: 32,
    
    direction: "down", // 現在の向き ("down", "up", "left", "right")
    moving: false,     // 移動中かどうか
    
    frameX: 0,         // 横のコマ番号 (0, 1, 2)
    frameY: 0,         // 縦の行番号 (0 または 1)
    animTimer: 0,
    animSpeed: 10,     // 切り替えスピード
    
    wasMoving: false,  // 直前のフレームで移動していたか
    idleStepCount: 0   // 停止アニメーションで進んだ総コマ数
};

// 歩行用と停止用、それぞれ4方向分の画像を定義
const images = {
    walkDown: new Image(),
    walkUp: new Image(),
    walkLeft: new Image(),
    walkRight: new Image(),
    idleDown: new Image(),
    idleUp: new Image(),
    idleLeft: new Image(),
    idleRight: new Image()
};

// 画像ファイルの割り当て
images.walkDown.src  = "player_sheet_F.png";
images.walkUp.src    = "player_sheet_B.png";
images.walkLeft.src  = "player_sheet_L.png";
images.walkRight.src = "player_sheet_R.png";

images.idleDown.src  = "player_sheet_Fstp.png";
images.idleUp.src    = "player_sheet_Fstp.png";
images.idleLeft.src  = "player_sheet_Fstp.png";
images.idleRight.src = "player_sheet_Fstp.png";

const keys = {};

window.addEventListener("keydown", (e) => { keys[e.key] = true; });
window.addEventListener("keyup", (e) => { keys[e.key] = false; });

// 更新処理
function update() {
    player.wasMoving = player.moving;
    player.moving = false;

    // 押されているキーに応じて向きと座標を更新（上下は0.5、左右は1）
    if (keys["ArrowUp"] || keys["w"]) {
        player.y -= 0.5;
        player.direction = "up";
        player.moving = true;
    } else if (keys["ArrowDown"] || keys["s"]) {
        player.y += 0.5;
        player.direction = "down";
        player.moving = true;
    } else if (keys["ArrowLeft"] || keys["a"]) {
        player.x -= 0.7;
        player.direction = "left";
        player.moving = true;
    } else if (keys["ArrowRight"] || keys["d"]) {
        player.x += 0.7;
        player.direction = "right";
        player.moving = true;
    }

    // 「歩行中から停止状態になった瞬間」に停止アニメーションをリセット
    if (player.wasMoving && !player.moving) {
        player.frameX = 0;
        player.frameY = 0;
        player.animTimer = 0;
        player.idleStepCount = 0; // 停止モーションのコマ経過数をリセット
    }

    // アニメーションの処理
    if (player.moving) {
        // 【移動中】歩行アニメーションをループ
        player.animTimer++;
        if (player.animTimer >= player.animSpeed) {
            player.animTimer = 0;
            player.frameX = (player.frameX + 1) % 3;
            if (player.frameX === 0) {
                player.frameY = (player.frameY === 0) ? 1 : 0;
            }
        }
    } else {
        // 【停止中】全6コマ（3コマ×2行）を1回だけ再生して停止する（上限を 6 に変更）
        if (player.idleStepCount < 6) {
            player.animTimer++;
            if (player.animTimer >= player.animSpeed) {
                player.animTimer = 0;
                
                // 次のコマへ進める
                player.frameX++;
                if (player.frameX >= 3) {
                    player.frameX = 0;
                    player.frameY = (player.frameY === 0) ? 1 : 0;
                }
                
                player.idleStepCount++;

                // ちょうど6コマ（1ループ完了）した瞬間に、最後のコマ（行1, 列2）でピタッと固定
                if (player.idleStepCount >= 6) {
                    player.frameX = 2;
                    player.frameY = 1;
                }
            }
        } else {
            // 1回ループ後は最後のコマ（行1, 列2）で固定
            player.frameX = 2;
            player.frameY = 1;
        }
    }
}

// 描画処理
function draw() {
    ctx.fillStyle = "#111122";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    let currentImg;
    if (player.moving) {
        if (player.direction === "down") currentImg = images.walkDown;
        else if (player.direction === "up") currentImg = images.walkUp;
        else if (player.direction === "left") currentImg = images.walkLeft;
        else if (player.direction === "right") currentImg = images.walkRight;
    } else {
        if (player.direction === "down") currentImg = images.idleDown;
        else if (player.direction === "up") currentImg = images.idleUp;
        else if (player.direction === "left") currentImg = images.idleLeft;
        else if (player.direction === "right") currentImg = images.idleRight;
    }

    if (currentImg && currentImg.complete && currentImg.naturalWidth !== 0) {
        ctx.drawImage(
            currentImg,
            player.frameX * player.width,  
            player.frameY * player.height, 
            player.width, player.height,
            Math.floor(player.x), Math.floor(player.y),
            player.width, player.height
        );
    } else {
        ctx.fillStyle = "#ff3366";
        ctx.fillRect(player.x, player.y, player.width, player.height);
    }
}

// メインループ
function loop() {
    update();
    draw();
    requestAnimationFrame(loop);
}

// 画像読み込み処理
let loadedCount = 0;
const totalImages = 8;

function onImageLoad() {
    loadedCount++;
    if (loadedCount >= totalImages) {
        loop();
    }
}

images.walkDown.onload = onImageLoad;
images.walkUp.onload = onImageLoad;
images.walkLeft.onload = onImageLoad;
images.walkRight.onload = onImageLoad;
images.idleDown.onload = onImageLoad;
images.idleUp.onload = onImageLoad;
images.idleLeft.onload = onImageLoad;
images.idleRight.onload = onImageLoad;

if (
    images.walkDown.complete &&
    images.walkUp.complete &&
    images.walkLeft.complete &&
    images.walkRight.complete &&
    images.idleDown.complete &&
    images.idleUp.complete &&
    images.idleLeft.complete &&
    images.idleRight.complete
) {
    loop();
}