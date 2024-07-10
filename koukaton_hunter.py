import math
import os
import random
import sys
import time
import pygame as pg
# from pygame.sprite import _Group


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

class Hunter(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 1.3)
    image = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): image,  # 右
        (+5, -5): pg.transform.rotozoom(image, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(image, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(image, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(image, -45, 0.9),  # 右下
    }

    def __init__(self,num: int, xy:tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        super().__init__()
        self.image = __class__.imgs[(+5, 0)]
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = xy
        self.dire = (+5, 0)
        self.flag = 1
        self.life = 15

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def brink(self):
        if self.life > 0:
            self.life -= 1
            self.flag = 2
            self.image.set_alpha(128)
            return True
        else:
            self.flag = 1
            self.life = 15
            self.image.set_alpha(255)
            return False



    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if sum_mv != [0, 0]:
            self.dire = tuple(sum_mv)
        # sum_mv[0] * self.flag
        # sum_mv[1] * self.flag
        self.rect.move_ip(sum_mv[0] * self.flag, sum_mv[1] * self.flag)
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.image = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.image, self.rect)

class Attack(pg.sprite.Sprite):
    """
     主人公の攻撃に関するクラス
    """
    def __init__(self, hunter:Hunter, skill: int):
        super().__init__()
        self.skill = skill
        self.life = 10
        self.flag = True
        self.image = pg.image.load(f"fig/effect{skill}.png")
        self.image = pg.transform.rotozoom(self.image, 180, 0.2)
        self.image1 = pg.transform.flip(self.image, 0, 1)
        self.rect = self.image.get_rect()
        self.rect.centery = hunter.rect.centery
        self.rect.centerx = hunter.rect.centerx
        self.rect.left = hunter.rect.right
        self.vx, self.vy = hunter.dire[0], hunter.dire[1]
        self.vxt, self.vyt = False, False
        self.sita = math.atan2(-self.vy, self.vx)
        self.sita1 = math.degrees(self.sita)
        self.image = pg.transform.rotozoom(self.image, self.sita1, 1)
        self.rect.centerx = hunter.rect.centerx + (hunter.rect.right - hunter.rect.left) * self.vx / 5
        self.rect.centery = hunter.rect.centery + (hunter.rect.bottom - hunter.rect.top) * self.vy / 5
        # self.rect.centerx = hunter.rect.centerx
        # self.rect.centery = hunter.rect.centery

    def update(self, hunter: Hunter):
        self.rect.centerx = hunter.rect.centerx + (hunter.rect.right - hunter.rect.left) * self.vx / 5
        self.rect.centery = hunter.rect.centery + (hunter.rect.bottom - hunter.rect.top) * self.vy / 5
        # self.rect.centerx = hunter.rect.centerx
        # self.rect.centery = hunter.rect.centery
        # if abs(self. vx) is 5:
        #     self.vyt = True
        # if abs(self.vy) is 5:
        #     self.vxt = True
        if self.life <= 5 and self.flag == True:
            self.flag = False
            self.image = self.image1
            self.image = pg.transform.rotozoom(self.image, self.sita1, 1)
            # self.image = pg.transform.flip(self.image, self.vxt, self.vyt)
        self.life -= 1
        if self.life < 0:
            self.kill()

        

class bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        image = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): image,  # 右
            (+1, -1): pg.transform.rotozoom(image, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(image, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(image, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(image, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        # self.state = "normal"
        # self.hyper_life = 0
        # self.value = 0

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        無敵の発動条件、発動時間、消費スコアの設定
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed * sum_mv[0], self.speed * sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed * sum_mv[0], -self.speed * sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", hunter: Hunter):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 hunter：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のhunterの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, hunter.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, hunter: Hunter, angle0: int = 0):
        """
        ビーム画像Surfaceを生成する
        引数 hunter：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = hunter.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle0
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = hunter.rect.centery+hunter.rect.height*self.vy
        self.rect.centerx = hunter.rect.centerx+hunter.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class NeoBeam(Beam):
    def __init__(self, hunter: Hunter, num: int):
        super().__init__(hunter)
        self.hunter = hunter
        self.num = num
        # NeoBeam.gen_beams(self)

    def gen_beams(self):
        bls = []
        bnum = range(-50, +51, 100 // (self.num - 1))
        for i in bnum:
            bls.append(Beam(self.hunter, i))
        return bls




class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        image = pg.image.load(f"fig/explosion.gif")
        self.imgs = [image, pg.transform.flip(image, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Gravity(pg.sprite.Sprite):
    def __init__(self, life: int):
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.rect = self.image.get_rect()
        pg.draw.rect(self.image, (0,0,0),(0, 0, WIDTH, HEIGHT))
        self.image.set_alpha(128)
        self.life = life    
    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()
        # screen.blit(self.image, self.rct)


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 400
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class Hyper:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self, hunter: Hunter, screen: pg.Surface):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 20)
        self.color = (128, 128, 128)
        self.word = "無敵"
        self.image = self.font.render(f"{self.word}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.centerx = hunter.rect.centerx + 50
        self.rect.centery = hunter.rect.centery - 50
        screen.blit(self.image, self.rect)

class Shield(pg.sprite.Sprite):
    """
    こうかとんの前に防御壁を出現させ、着弾を防ぐクラス
    """
    def __init__(self, hunter: Hunter, life: int):
        super().__init__()
        self.size = (20, hunter.rect.height*2)  # 大きさのタプル
        self.image = pg.Surface(self.size)  # 空のSurfaceを作成
        self.life = life  # 発動時間の設定
        self.color = (0, 0, 255)  # 矩形の色を青色に指定
        pg.draw.rect(self.image, self.color, (0, 0, 20, hunter.rect.height*2))
        self.vx, self.vy = hunter.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(self.image, angle, 1.0)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.centery = hunter.rect.centery+hunter.rect.height*self.vy
        self.rect.centerx = hunter.rect.centerx+hunter.rect.width*self.vx

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()


class Emp:
    """
    enmを発動
    引数 bombs:Bombインスタンスグループ emys:Enemyインスタンスグループ
         screen:画面Surface
    """
    def __init__(self, bombs: pg.sprite.Group, emys:pg.sprite.Group, screen: pg.Surface):
        for emy in emys:
            emy.interval = math.inf
            emy.image = pg.transform.laplacian(emy.image)
            emy.image.set_colorkey((0,0,0))
        for bomb in bombs:
            bomb.speed /= 2
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect = (self.image, (255, 255, 0), (0, 0, 1600, 900))
        self.image.set_alpha(100)
        screen.blit(self.image, [0, 0])
        time.sleep(0.05)
        pg.display.update()


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    hunter = Hunter(3, (900, 400))
    aa = pg.sprite.Group()
    skill = pg.sprite.Group()
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    shields = pg.sprite.Group() 
    gravity = pg.sprite.Group()

    tmr = 0
    cl = 50
    clock = pg.time.Clock()
    state = "normal"
    bflag = False
    hyper_life = 10
    while True:
        aflag = False
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if not aflag:
                    aflag = True
                    aa.add(Attack(hunter, 1))
            if event.type == pg.KEYDOWN and event.key == pg.K_LSHIFT:
                bflag = True
            # if event.type == pg.KEYDOWN and event.key == pg.K_c:
            #     if score.value >= 50 and len(shields) == 0:
            #         shields.add(Shield(hunter, 400))
            #         score.value -= 50
            # if event.type == pg.KEYDOWN and event.key == pg.K_e:
            #     if score.value >= 20:  #電磁パルス
            #         Emp(bombs, emys, screen)
            #         score.value -= 20

            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                if not aflag:
                    aflag = True
                    skill.add(Attack(hunter, 2))
            #無敵発動する方法と条件
        #     if key_lst[pg.K_RSHIFT] and score.value >= 100 and state == "normal":
        #         state = "hyper"
        #         hyper_life = 500
        #         score.value -= 100
        #     #無敵発動中の状態
        # if state == "hyper":
        #     hunter.image = pg.transform.laplacian(hunter.image)
        #     hyper_life -= 1
        #     if hyper_life < 0:
        #         state = "normal"
                    # image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)  # 元の画像に戻す

            # screen.blit(image, pg.rect)
        screen.blit(bg_img, [0, 0])

        if tmr%100 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, hunter))

        for emy in pg.sprite.groupcollide(emys, aa or skill, True, False).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            # k_hp.damage()
            score.value += 10  # 10点アップ
            hunter.change_img(6, screen)  # こうかとん喜びエフェクト

        # for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
        #     exps.add(Explosion(bomb, 50))  # 爆発エフェクト
        #     score.value += 1  # 1点アップ
        
        # for shield in pg.sprite.groupcollide(bombs, shields, True, True).keys():
        #     exps.add(Explosion(shield, 50))  # 爆発エフェクト
        #     score.value += 1  # 1点アップ

        # for bomb in pg.sprite.groupcollide(bombs, gravity, True, False).keys():
        #     exps.add(Explosion(bomb, 50))

        # for emy in pg.sprite.groupcollide(emys, gravity, True, False).keys():
        #     exps.add(Explosion(emy, 50))

        for emy in pg.sprite.spritecollide(hunter, emys, False):
            if state == "nomal":
                hunter.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return

        for bomb in pg.sprite.spritecollide(hunter, bombs, False):
            if state == "normal":
                hunter.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            
        if bflag == True:
            bflag = hunter.brink()
            state = "hyper"
            cl = 40
            Hyper(hunter, screen)
        else:
            state = "nomal"
        hunter.update(key_lst, screen)
        # beams.update()
        # beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        aa.update(hunter)
        skill.update(hunter)
        aa.draw(screen)
        skill.draw(screen)
        # gravity.update()
        # gravity.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        # shields.update()
        # shields.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(cl)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
