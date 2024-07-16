
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
    ゲームキャラクター（Hunter）に関するクラス
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
        Hunter画像Surfaceを生成する
        引数 xy：Hunter画像の初期位置座標タプル
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
        Hunter画像を切り替え，画面に転送する
        引数1 num：Hunter画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def brink(self):
        """
        Hunterのジャスト回避の設定
        """
        if self.life > 0:
            self.life -= 1
            self.flag = 2
            # self.image.set_alpha(128)
            return True
        else:
            self.flag = 1
            self.life = 15
            self.image.set_alpha(255)
            return False



    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてHunterを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        無敵の発動条件、発動時間、消費スコアの設定
        無敵の発動条件、発動時間、消費スコアの設定
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
     Hunterの攻撃に関するクラス
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

        

class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Monster", hunter:Hunter):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 hunter：攻撃対象のこうかとん
        """
        super().__init__()
        rad = (100)  # 爆弾円の半径：75
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のhunterの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, hunter.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 15

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Monster", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
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
        # screen.blit(self.img, self.rct)


class Monster(pg.sprite.Sprite):
    """
    こうかとんに関するクラス
    """
    imgs = [pg.image.load(f"fig/9.png")]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(WIDTH/2 - 100, WIDTH/2 + 1-00), random.randint(HEIGHT/2 - 100,HEIGHT/2 + 100)
        self.vx, self.vy = 0,0
        #self.bound = random.randint(50, HEIGHT)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = 100  # 攻撃インターバル
        self.flag = True


    def update(self,tmr):
        if self.flag == True:
            self.vx = 0
            self.vy = 0
            self.state = "stop"
            if tmr%300 <= 1:
                self.flag = False
        if self.flag == False:
            self.vx = random.randint(-150,150)  #x座標移動
            if self.rect.centerx-50 >= WIDTH:
                self.vx = random.randint(-150,-180)
            if self.rect.centerx+50 <= 0:
                self.vx = random.randint(150,180)

            self.vy = random.randint(-150,150)  #y座標移動
            if self.rect.centery-50 >= HEIGHT:
                self.vy = random.randint(-150,-180)
            if self.rect.centery+50 <= 0:
                self.vy = random.randint(150,180)
        self.rect.move_ip(self.vx, self.vy)
        if not self.flag:
            self.flag = True
class Atk1(pg.sprite.Sprite):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    def __init__(self, emy:"Monster"):
        super().__init__()
        rad = (200)  
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors) 
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery
        print(self.rect.centerx,emy.rect.centerx)
    

    def update(self,tmr):
        if tmr%300 ==100:
            self.kill()


class item_h(pg.sprite.Sprite):
    """"
    回復薬の管理
    """
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
        self.color = (0, 180, 0)
        self.value = 3
        self.image = self.font.render(f"回復薬: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 1010, HEIGHT-100

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"回復薬: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class item_k(pg.sprite.Sprite):
    """"
    強走薬の管理
    """
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
        self.color = (255, 255, 0)
        self.value = 3
        self.image = self.font.render(f"強走薬: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 1010, HEIGHT-60

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"強走薬: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class item_a(pg.sprite.Sprite):
    """"
    鬼人薬の管理
    """
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
        self.color = (255, 0, 0)
        self.value = 3
        self.image = self.font.render(f"鬼人薬: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 1010, HEIGHT-20

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"鬼人薬: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class item_a_efe():
    """"
    鬼人薬のエフェクト
    """
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
        self.color = (255, 0, 0)
        self.image = self.font.render(f"UP中！", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 800, HEIGHT-20

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"UP中！", 0, self.color)
        screen.blit(self.image, self.rect)


class item_h(pg.sprite.Sprite):
    """"
    回復薬の管理
    """
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
        self.color = (0, 180, 0)
        self.value = 3
        self.image = self.font.render(f"回復薬: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 1010, HEIGHT-100

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"回復薬: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class item_k(pg.sprite.Sprite):
    """"
    強走薬の管理
    """
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
        self.color = (255, 255, 0)
        self.value = 3
        self.image = self.font.render(f"強走薬: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 1010, HEIGHT-60

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"強走薬: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class item_a(pg.sprite.Sprite):
    """"
    鬼人薬の管理
    """
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
        self.color = (255, 0, 0)
        self.value = 3
        self.image = self.font.render(f"鬼人薬: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 1010, HEIGHT-20

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"鬼人薬: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class item_a_efe():
    """"
    鬼人薬のエフェクト
    """
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
        self.color = (255, 0, 0)
        self.image = self.font.render(f"UP中！", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 800, HEIGHT-20

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"UP中！", 0, self.color)
        screen.blit(self.image, self.rect)


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 400
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

        self.value = 400
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class Shield(pg.sprite.Sprite):
    """
    こうかとんの前に防御壁を出現させ、着弾を防ぐクラス
    """
    def __init__(self, hunter:Hunter, life: int):
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

    def update(self, screen):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class Hyper:
    """
    ジャスト回避時に付与する無敵を視覚的に表示するクラス。
    """
    def __init__(self, hunter: Hunter, screen: pg.Surface):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 20)
        self.img = pg.Surface([WIDTH, HEIGHT])
        pg.draw.rect(self.img, [200, 200, 200], [0, 0, WIDTH, HEIGHT])
        self.img.set_alpha(64)
        self.color = (128, 128, 128)
        self.word = "無敵"
        self.image = self.font.render(f"{self.word}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.centerx = hunter.rect.centerx + 50
        self.rect.centery = hunter.rect.centery - 50
        screen.blit(self.image, self.rect)
        screen.blit(self.img, [0, 0])
        

class HP:
    """
    HPを管理するクラス
    引数 hp:HPの設定値int name:HPバーに表示する名前str
         xy:HPバーを表示する左端中央の座標(int, int) sz:Hpバーのサイズint
    """
    def __init__(self, hp: int, name: str, xy: tuple, sz: int):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", sz)
        self.color = (0, 200, 0)
        self.max_hp = hp
        self.hp = hp
        self.name = name
        self.x = xy[0]
        self.y = xy[1]
        self.size = sz*30, sz*2
        self.image1 = pg.Surface(self.size)
        pg.draw.rect(self.image1, (0, 0, 0), (0, 0, self.size[0], self.size[1]))
        pg.draw.rect(self.image1, self.color, (0, 0, self.size[0]*self.hp/self.max_hp, self.size[1]))
        self.image2 = self.font.render(f"{self.name} : {self.hp}/{self.max_hp}", 0, (255, 255, 255))
        self.rect1 = self.image1.get_rect()
        self.rect2 = self.image2.get_rect()
        self.rect1.midleft = self.x, self.y
        self.rect2.midleft = self.x, self.y

    def damage(self, damege: int):  # ダメージを受けた時のメソッド
        self.hp -= damege
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        elif self.hp < 0:
            self.hp = 0

    def update(self, screen: pg.Surface):  # HPゲージの更新
        if self.hp <= (self.max_hp*0.5):
            self.color = (200, 200, 0)
        if self.hp <= (self.max_hp*0.2):
            self.color = (200, 0, 0)
        pg.draw.rect(self.image1, (0, 0, 0), (0, 0, self.size[0], self.size[1]))
        pg.draw.rect(self.image1, self.color, (0, 0, self.size[0]*self.hp/self.max_hp, self.size[1]))
        self.image2 = self.font.render(f"{self.name} : {self.hp}/{self.max_hp}", 0, (255, 255, 255))
        screen.blit(self.image1, self.rect1)
        screen.blit(self.image2, self.rect2)


class SP:
    """
    スタミナを管理するクラス
    引数 sp:HPの設定値int xy:HPバーを表示する左端中央の座標(int, int) 
         sz:Hpバーのサイズint
    """
    def __init__(self, sp: int, xy: tuple, sz: int):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", sz)
        self.color = (240, 120, 0)
        self.max_sp = sp
        self.sp = sp
        self.nsp = 0.25
        self.x = xy[0]
        self.y = xy[1]
        self.size = sz*25, sz
        self.image1 = pg.Surface(self.size)
        pg.draw.rect(self.image1, (0, 0, 0), (0, 0, self.size[0], self.size[1]))
        pg.draw.rect(self.image1, self.color, (0, 0, self.size[0]*self.sp/self.max_sp, self.size[1]))
        self.image2 = self.font.render(f"SP: {self.sp}/{self.max_sp}", 0, (255, 255, 255))
        self.rect1 = self.image1.get_rect()
        self.rect2 = self.image2.get_rect()
        self.rect1.midleft = self.x, self.y+sz*2
        self.rect2.midleft = self.x, self.y+sz*2

    def pay_sp(self, damege: int):  # スタミナを消費した時のメソッド
        if self.sp > self.max_sp:
            self.sp = self.max_sp
        elif self.sp-damege < 0:
            self.sp = 0
        else:
            self.sp -= damege

    def update(self, screen: pg.Surface):  # SPゲージの更新
        if self.sp == self.max_sp:
            self.nsp = 0.25
        elif self.sp <= 5:
            self.nsp = 0.125
        self.sp += self.nsp
        if self.sp > self.max_sp:
            self.sp = self.max_sp
        pg.draw.rect(self.image1, (0, 0, 0), (0, 0, self.size[0], self.size[1]))
        pg.draw.rect(self.image1, self.color, (0, 0, self.size[0]*self.sp/self.max_sp, self.size[1]))
        self.image2 = self.font.render(f"SP: {int(self.sp)}/{self.max_sp}", 0, (255, 255, 255))
        screen.blit(self.image1, self.rect1)
        screen.blit(self.image2, self.rect2)


def main():
    pg.display.set_caption("こうかとん狩猟DX")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    Item_h = item_h()
    Item_k = item_k()
    Item_a = item_a()

    Item_h = item_h()
    Item_k = item_k()
    Item_a = item_a()

    hunter = Hunter(3, (900, 400))
    aa = pg.sprite.Group()
    skill = pg.sprite.Group()
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    shields = pg.sprite.Group() 
    gravity = pg.sprite.Group()
    Item_a_efe = item_a_efe()
    atk1 = pg.sprite.Group()

    tmr = 0
    cl = 50

    k_hp = HP(1000, "Massun", (30, 100), 12)
    k_sp = SP(100, (30, 100), 12)
    e_hp = HP(15000, "コウカトン", (240, 40), 20)
    Item_a_efe = item_a_efe()

    at = 1
    add_sp = 0
    a_co = 500
    sp_co = 500
    tmr = 0
    clock = pg.time.Clock()
    state = "normal"
    bflag = False
    hyper_life = 10
    emys.add(Monster())
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
                    if k_sp.sp >= 30:
                        k_sp.pay_sp(30)
                        aflag = True
                        skill.add(Attack(hunter, 2))

            if event.type == pg.KEYDOWN and event.key == pg.K_i:   #回復薬
                if Item_h.value >= 1:
                    if k_hp.hp <= 700:
                        Item_h.value -= 1
                        k_hp.damage(-300)       
            if event.type == pg.KEYDOWN and event.key == pg.K_k:   #強走薬
                if Item_k.value >= 1:
                    k_sp.max_sp = 200
                    k_sp.sp += 100
                    add_sp = 2 
                    Item_k.value -= 1
            if event.type == pg.KEYDOWN and event.key == pg.K_j:   #鬼人薬
                if Item_a.value >= 1:
                    Item_a.value -= 1
                    at = 2         #攻撃力UP
        if add_sp == 2:
                sp_co -= 1
                if sp_co <= 0:
                    k_sp.max_sp = 100
                    add_sp = 1
                    sp_co = 500
        if at == 2:
                a_co -= 1
                if a_co <= 0:
                    at = 1
                    a_co = 500
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


        for emy in emys:
            if emy.state == "stop" and tmr%(5*emy.interval) == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, hunter))

            if tmr%(3*emy.interval) == 0:
                atk1.add(Atk1(emy))
            

        for emy in pg.sprite.groupcollide(emys, aa, False, False).keys():
            e_hp.damage(6 * at)
            if e_hp.hp == 0:
                color = [255, 255, 255]
                font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 20)
                word = "GameClear"
                image = font.render(f"{word}", 0, color)
                image.blit(screen, [WIDTH / 2, HEIGHT / 2])
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            
        for emy in pg.sprite.groupcollide(emys, skill, False, False).keys():
            e_hp.damage(18 * at)
            if e_hp.hp == 0:
                color = [255, 255, 255]
                font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 20)
                word = "GameClear"
                image = font.render(f"{word}", 0, color)
                image.blit(screen, [WIDTH / 2, HEIGHT / 2])
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ
        
        for shield in pg.sprite.groupcollide(bombs, shields, True, True).keys():
            exps.add(Explosion(shield, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for bomb in pg.sprite.groupcollide(bombs, gravity, True, False).keys():
            exps.add(Explosion(bomb, 50))

        for emy in pg.sprite.groupcollide(emys, gravity, True, False).keys():
            exps.add(Explosion(emy, 50))

        for emy in pg.sprite.spritecollide(hunter,atk1,False):
            k_hp.damage(5)
            if k_hp.hp == 0:
                    hunter.change_img(8, screen) # こうかとん悲しみエフェクト
                    score.update(screen)
                    pg.display.update()
                    time.sleep(2)
                    return


        for bomb in pg.sprite.spritecollide(hunter, bombs, True):
            if state == "hyper":
                exps.add(Explosion(bomb, 50))
            if state == "normal":
                k_hp.damage(150)
                if k_hp.hp == 0:
                    hunter.change_img(8, screen) # こうかとん悲しみエフェクト
                    score.update(screen)
                    pg.display.update()
                    time.sleep(2)
                    return
        
        
        if bflag == True:
            bflag = hunter.brink()
            state = "hyper"
            cl = 30
            Hyper(hunter, screen)
        else:
            state = "normal"
            cl = 50
            
        tmr += 1
        atk1.update(tmr)
        atk1.draw(screen)
        hunter.update(key_lst, screen)
        aa.update(hunter)
        skill.update(hunter)
        aa.draw(screen)
        skill.draw(screen)
        beams.update()
        beams.draw(screen)
        emys.update(tmr)
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        # gravity.update()
        # gravity.draw(screen)
        # exps.update()
        # exps.draw(screen)
        score.update(screen)
        Item_h.update(screen)
        Item_k.update(screen)
        Item_a.update(screen)
        if at == 2:
            Item_a_efe.update(screen)
        k_hp.update(screen)
        k_sp.update(screen)
        e_hp.update(screen)
        # shields.update()
        # shields.draw(screen)
        pg.display.update()
        clock.tick(cl)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()