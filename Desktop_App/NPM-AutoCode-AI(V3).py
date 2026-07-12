"""
NPMAI Agent Desktop — v4 (npmai_agents edition)

Here it is about Desktop APP.
"""
import sys, os, math, random, threading
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from npmai_agents import AgentBrain, Workspace, CredStore

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QLineEdit, QPushButton, QFrame, QScrollArea,
    QStackedWidget, QSizePolicy, QGraphicsOpacityEffect,
    QTabWidget, QDialog, QDialogButtonBox, QMessageBox,
    QGroupBox
)
from PySide6.QtCore import (
    QThread, Signal, Qt, QTimer, QPointF, QRectF, QRect,
    QPropertyAnimation, QEasingCurve,
)
from PySide6.QtGui import (
    QFont, QColor, QPalette, QLinearGradient, QPainter, QBrush, QPen,
    QPainterPath, QRadialGradient,
)

P = {
    "void":   "#04030C", "deep":  "#080618", "space": "#0D0B20",
    "panel":  "#111028", "lift":  "#171530", "ridge": "#1E1C38",
    "rim":    "#2A2748", "glow":  "#3D3960",
    "mint":   "#2AFFA0", "cyan":  "#00E5FF", "violet":"#A78BFA",
    "rose":   "#FF6B9D", "amber": "#FFB347", "sky":   "#38BDF8",
    "bright": "#F0EEFF", "mid":   "#8E8AAE", "dim":   "#4E4B6A",
    "ghost":  "#2A2744",
}

_TASK_KEYWORDS = [
    "file", "folder", "git", "github", "gitlab", "docker", "kubernetes", "k8s",
    "terraform", "aws", "s3", "lambda", "cloudflare", "vercel", "netlify", "railway",
    "stripe", "razorpay", "shopify", "invoice", "crm", "inventory", "contract",
    "email", "smtp", "teams", "zoom", "twilio", "sendgrid", "webhook", "calendar",
    "notion", "linear", "asana", "trello", "clickup", "todoist", "obsidian",
    "figma", "blender", "svg", "canva", "diagram", "3d",
    "scrape", "download", "screenshot", "database", "report", "chart",
    "ffmpeg", "youtube", "audio", "video", "image", "resize", "convert", "podcast",
    "ssh", "terminal", "run command", "backup", "zip", "unzip", "schedule",
    "encrypt", "scan", "deploy", "network", "printer", "clipboard",
]


def _looks_like_task(text: str) -> bool:
    words = text.strip().split()
    if len(words) > 6:
        return True
    lower = text.lower()
    return any(kw in lower for kw in _TASK_KEYWORDS)


class AgentWorker(QThread):
    log_sig      = Signal(str)
    progress_sig = Signal(int)
    status_sig   = Signal(str)
    done_sig     = Signal(bool, str)
    bubble_sig   = Signal(str, bool)

    def __init__(self, task: str):
        super().__init__()
        self.task     = task
        self._killed  = [False]
        self._brain   = None

    def kill(self):
        self._killed[0] = True
        if self._brain and self._brain.executor:
            self._brain.executor.kill()

    def run(self):
        self._brain = AgentBrain(
            log_cb      = self.log_sig.emit,
            progress_cb = self.progress_sig.emit,
            status_cb   = self.status_sig.emit,
        )
        if _looks_like_task(self.task):
            ok = self._brain.run_task(self.task, killed_flag=self._killed)
            msg = "✓ Task completed!" if ok else "✗ Task failed."
            self.bubble_sig.emit(msg, True)
            self.done_sig.emit(ok, msg)
        else:
            resp = self._brain.chat(self.task)
            self.bubble_sig.emit(resp, True)
            self.progress_sig.emit(100)
            self.done_sig.emit(True, resp)


class CosmicBG(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._phase = 0.0
        self._particles = self._init_particles(140)
        self._orbs = [
            (0.12, 0.22, 460, QColor(42,255,160,20),  0.007, 0.0),
            (0.82, 0.38, 380, QColor(167,139,250,16), 0.005, 2.1),
            (0.50, 0.78, 310, QColor(0,229,255,14),   0.009, 4.2),
            (0.28, 0.68, 260, QColor(255,107,157,12), 0.006, 1.0),
            (0.88, 0.82, 210, QColor(255,179,71,11),  0.011, 3.3),
        ]
        QTimer(self, timeout=self._tick, interval=16).start()

    def _init_particles(self, n):
        cols = ["#2AFFA0","#00E5FF","#A78BFA","#FF6B9D","#FFB347","#38BDF8"]
        return [{"x":random.random(),"y":random.random(),
                 "vx":(random.random()-0.5)*0.35,"vy":(random.random()-0.5)*0.35,
                 "r":random.random()*1.6+0.3,
                 "col":QColor(random.choice(cols)),
                 "ba":random.randint(50,150),
                 "life":random.random()} for _ in range(n)]

    def _tick(self):
        self._phase = (self._phase + 0.011) % (math.pi * 2)
        w,h = max(self.width(),1), max(self.height(),1)
        for p in self._particles:
            p["x"] += p["vx"]/w*100; p["y"] += p["vy"]/h*100
            p["life"] += 0.003
            if p["x"]<0 or p["x"]>1 or p["y"]<0 or p["y"]>1 or p["life"]>1:
                p["x"]=random.random(); p["y"]=random.random(); p["life"]=0
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(), self.height()
        p.fillRect(0,0,w,h, QColor(P["void"]))
        for cx_r,cy_r,r,col,spd,off in self._orbs:
            cx = cx_r*w + math.sin(self._phase*spd*80+off)*55
            cy = cy_r*h + math.cos(self._phase*spd*60+off)*40
            g = QRadialGradient(cx,cy,r); g.setColorAt(0,col)
            outer=QColor(col); outer.setAlpha(0); g.setColorAt(1,outer)
            p.fillRect(0,0,w,h,QBrush(g))
        p.setPen(QPen(QColor(255,255,255,4),1))
        for gx in range(0,w+70,70): p.drawLine(gx,0,gx,h)
        for gy in range(0,h+70,70): p.drawLine(0,gy,w,gy)
        p.setPen(Qt.NoPen)
        for pt in self._particles:
            a = int(pt["ba"]*abs(math.sin(self._phase*1.4+pt["life"]*8)))
            c=QColor(pt["col"]); c.setAlpha(max(15,min(200,a)))
            p.setBrush(c); p.drawEllipse(QPointF(pt["x"]*w,pt["y"]*h),pt["r"],pt["r"])
        vg=QRadialGradient(w/2,h/2,max(w,h)*0.72)
        vg.setColorAt(0,QColor(0,0,0,0)); vg.setColorAt(1,QColor(0,0,0,165))
        p.fillRect(0,0,w,h,QBrush(vg)); p.end()

class GlowCard(QWidget):
    def __init__(self, parent=None, accent="#2AFFA0", radius=18, alpha=205):
        super().__init__(parent)
        self._accent=QColor(accent); self._radius=radius
        self._alpha=alpha; self._glow=0.0; self._hover=False
        self.setAttribute(Qt.WA_TranslucentBackground)
        QTimer(self,timeout=self._anim,interval=16).start()

    def _anim(self):
        t=1.0 if self._hover else 0.0
        self._glow += (t-self._glow)*0.09
        if abs(self._glow-t)>0.01: self.update()

    def enterEvent(self,e): self._hover=True
    def leaveEvent(self,e): self._hover=False

    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        rect=self.rect().adjusted(2,2,-2,-2)
        path=QPainterPath(); path.addRoundedRect(QRectF(rect),self._radius,self._radius)
        p.setClipPath(path)
        p.fillPath(path,QColor(17,16,40,self._alpha))
        sh=QLinearGradient(0,rect.top(),0,rect.top()+55)
        sh.setColorAt(0,QColor(255,255,255,13)); sh.setColorAt(1,QColor(255,255,255,0))
        p.fillPath(path,QBrush(sh)); p.setClipping(False)
        a=QColor(self._accent); border_a=int(50+(180-50)*self._glow)
        a.setAlpha(border_a); p.setPen(QPen(a,1.5)); p.drawPath(path)
        if self._glow>0.05:
            for ring in range(3):
                exp=(ring+1)*3
                hp=QPainterPath()
                hp.addRoundedRect(QRectF(rect.adjusted(-exp,-exp,exp,exp)),
                                  self._radius+exp,self._radius+exp)
                ha=int(28*self._glow/(ring+1))
                hc=QColor(self._accent.red(),self._accent.green(),self._accent.blue(),ha)
                p.setPen(QPen(hc,1)); p.setBrush(Qt.NoBrush); p.drawPath(hp)
        p.end()

class PulseBtn(QPushButton):
    def __init__(self, text, accent="#2AFFA0", dark_text=True, parent=None):
        super().__init__(text,parent)
        self._ac=QColor(accent); self._dt=dark_text
        self._h=0.0; self._pulse=0.0; self._pd=1; self._press=False
        self.setCursor(Qt.PointingHandCursor); self.setFixedHeight(48)
        self.setFont(QFont("Segoe UI",12,QFont.Bold))
        QTimer(self,timeout=self._tick,interval=16).start()

    def _tick(self):
        self._pulse+=0.035*self._pd
        if self._pulse>=1: self._pd=-1
        if self._pulse<=0: self._pd=1
        self.update()

    def enterEvent(self,e): self._h=1.0
    def leaveEvent(self,e): self._h=0.0
    def mousePressEvent(self,e): self._press=True; super().mousePressEvent(e)
    def mouseReleaseEvent(self,e): self._press=False; super().mouseReleaseEvent(e)

    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r=self.rect(); path=QPainterPath()
        path.addRoundedRect(QRectF(r.adjusted(1,1,-1,-1)),13,13)
        g=QLinearGradient(r.left(),r.top(),r.right(),r.bottom())
        base=QColor(self._ac)
        light=base.darker(110) if self._press else base.lighter(int(108+self._h*14+self._pulse*8))
        g.setColorAt(0,base); g.setColorAt(1,light)
        p.fillPath(path,QBrush(g))
        ga=int((0.3+self._pulse*0.2+self._h*0.25)*255*0.4)
        for ring in range(3):
            exp=(ring+1)*3; hp=QPainterPath()
            hp.addRoundedRect(QRectF(r.adjusted(-exp+1,-exp+1,exp-1,exp-1)),13+exp,13+exp)
            hc=QColor(self._ac.red(),self._ac.green(),self._ac.blue(),max(0,ga//(ring+1)))
            p.setPen(QPen(hc,1)); p.setBrush(Qt.NoBrush); p.drawPath(hp)
        p.setPen(QColor("#050310") if self._dt else QColor(P["bright"]))
        p.setFont(self.font()); p.drawText(r,Qt.AlignCenter,self.text()); p.end()

class GhostBtn(QPushButton):
    def __init__(self,text,accent="#2AFFA0",parent=None):
        super().__init__(text,parent); self._ac=QColor(accent); self._h=0.0
        self.setCursor(Qt.PointingHandCursor); self.setFixedHeight(48)
        self.setFont(QFont("Segoe UI",11,QFont.DemiBold))
        QTimer(self,timeout=self.update,interval=16).start()

    def enterEvent(self,e): self._h=1.0
    def leaveEvent(self,e): self._h=0.0

    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r=self.rect(); path=QPainterPath()
        path.addRoundedRect(QRectF(r.adjusted(1,1,-1,-1)),13,13)
        p.fillPath(path,QColor(self._ac.red(),self._ac.green(),self._ac.blue(),int(self._h*30)))
        ba=int(70+self._h*150)
        p.setPen(QPen(QColor(self._ac.red(),self._ac.green(),self._ac.blue(),ba),1.5))
        p.drawPath(path)
        tc=QColor(self._ac) if self._h>0.3 else QColor(P["mid"])
        p.setPen(tc); p.setFont(self.font()); p.drawText(r,Qt.AlignCenter,self.text()); p.end()

class GlowInput(QLineEdit):
    def __init__(self,placeholder="",parent=None):
        super().__init__(parent); self.setPlaceholderText(placeholder)
        self.setFixedHeight(52); self.setFont(QFont("Segoe UI",12))
        self._focused=False; self._g=0.0
        QTimer(self,timeout=self._tick,interval=16).start()

    def _tick(self):
        t=1.0 if self._focused else 0.0
        self._g+=(t-self._g)*0.1
        self.setStyleSheet(f"""
            QLineEdit{{background:rgba(14,12,32,{int(185+self._g*40)});
            border:1.5px solid rgba({int(42+self._g*160)},{int(142+self._g*100)},{int(self._g*60+180)},{int(80+self._g*175)});
            border-radius:13px;padding:0 18px;color:{P['bright']};font-size:12px;
            selection-background-color:rgba(42,255,160,80);}}
            QLineEdit::placeholder{{color:{P['dim']};}}""")

    def focusInEvent(self,e): self._focused=True; super().focusInEvent(e)
    def focusOutEvent(self,e): self._focused=False; super().focusOutEvent(e)

class GlowProgress(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.setFixedHeight(7)
        self._val=0.0; self._target=0.0; self._phase=0.0
        QTimer(self,timeout=self._tick,interval=16).start()

    def set_value(self,v): self._target=v

    def _tick(self):
        self._val+=(self._target-self._val)*0.07
        self._phase+=0.05; self.update()

    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        tp=QPainterPath(); tp.addRoundedRect(QRectF(0,0,w,h),h/2,h/2)
        p.fillPath(tp,QColor(P["ridge"]))
        fw=w*self._val/100
        if fw>2:
            fp=QPainterPath(); fp.addRoundedRect(QRectF(0,0,fw,h),h/2,h/2)
            g=QLinearGradient(0,0,fw,0)
            g.setColorAt(0,QColor("#2AFFA0")); g.setColorAt(0.5,QColor("#00E5FF"))
            g.setColorAt(1,QColor("#A78BFA")); p.fillPath(fp,QBrush(g))
            sx=fw*(0.5+math.sin(self._phase)*0.5)
            sg=QRadialGradient(sx,h/2,fw*0.3)
            sg.setColorAt(0,QColor(255,255,255,55)); sg.setColorAt(1,QColor(255,255,255,0))
            p.setClipPath(fp); p.fillRect(QRectF(0,0,fw,h),QBrush(sg)); p.setClipping(False)
        p.end()

class ChatBubble(QWidget):
    def __init__(self, text:str, is_agent:bool, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        lay = QHBoxLayout(self); lay.setContentsMargins(8,4,8,4)
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setFont(QFont("Segoe UI",12))
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble.setMaximumWidth(680)
        bubble.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Minimum)
        if is_agent:
            bubble.setStyleSheet(f"""QLabel{{background:rgba(17,16,40,220);
                border:1px solid rgba(42,255,160,80);
                border-radius:16px;border-top-left-radius:4px;
                padding:12px 16px;color:{P['bright']};line-height:1.6;}}""")
            lay.addWidget(bubble); lay.addStretch()
        else:
            bubble.setStyleSheet(f"""QLabel{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 rgba(42,255,160,40),stop:1 rgba(0,229,255,30));
                border:1px solid rgba(42,255,160,120);
                border-radius:16px;border-top-right-radius:4px;
                padding:12px 16px;color:{P['bright']};}}""")
            lay.addStretch(); lay.addWidget(bubble)
        eff = QGraphicsOpacityEffect(bubble); bubble.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff,b"opacity",self)
        anim.setDuration(350); anim.setStartValue(0); anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.OutCubic); anim.start()
        self._anim = anim

class NavBtn(QWidget):
    clicked = Signal(int)
    ICONS  = ["💬","📋","🛠","⚙","👤","📖"]
    LABELS = ["Agent","History","Tools","Settings","Founder","Docs"]
    COLORS = [P["mint"],P["cyan"],P["amber"],P["violet"],P["rose"],P["sky"]]

    def __init__(self,idx,parent=None):
        super().__init__(parent); self._idx=idx
        self._active=False; self._h=0.0; self._hf=False
        self.setCursor(Qt.PointingHandCursor); self.setFixedHeight(58)
        self.setAttribute(Qt.WA_TranslucentBackground)
        QTimer(self,timeout=self._tick,interval=16).start()

    def _tick(self):
        t=1.0 if self._hf else 0.0
        self._h+=(t-self._h)*0.1; self.update()

    def set_active(self,v): self._active=v; self.update()
    def enterEvent(self,e): self._hf=True
    def leaveEvent(self,e): self._hf=False
    def mousePressEvent(self,e): self.clicked.emit(self._idx)

    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        col=QColor(self.COLORS[self._idx])
        blend=1.0 if self._active else self._h
        if blend>0.01:
            path=QPainterPath()
            path.addRoundedRect(QRectF(8,5,w-16,h-10),11,11)
            p.fillPath(path,QColor(col.red(),col.green(),col.blue(),int(blend*(60 if self._active else 35))))
            if self._active:
                p.setPen(QPen(QColor(col.red(),col.green(),col.blue(),110),1.5))
                p.drawPath(path)
        if self._active:
            bar=QPainterPath(); bar.addRoundedRect(QRectF(0,h*0.2,3,h*0.6),2,2)
            p.fillPath(bar,col)
            bg=QRadialGradient(1,h/2,22)
            bg.setColorAt(0,QColor(col.red(),col.green(),col.blue(),75))
            bg.setColorAt(1,QColor(col.red(),col.green(),col.blue(),0))
            p.fillRect(0,0,30,h,QBrush(bg))
        p.setFont(QFont("Segoe UI",16))
        p.setPen(col if (self._active or blend>0.3) else QColor(P["mid"]))
        p.drawText(QRect(14,0,34,h),Qt.AlignVCenter|Qt.AlignLeft,self.ICONS[self._idx])
        p.setPen(QColor(P["bright"]) if (self._active or blend>0.3) else QColor(P["mid"]))
        p.setFont(QFont("Segoe UI",11,QFont.Bold if self._active else QFont.Normal))
        p.drawText(QRect(52,0,w-60,h),Qt.AlignVCenter|Qt.AlignLeft,self.LABELS[self._idx])
        p.end()
        
class LoginDialog(QDialog):
    """Email/password only, per spec. Appears only when the user clicks
    'Get MCP Link' — never blocks any other part of the app."""

    def __init__(self, link_mgr, parent=None):
        super().__init__(parent)
        self._mgr = link_mgr
        self.setWindowTitle("Log in — MCP Link")
        self.setFixedSize(360, 260)
        self.setStyleSheet(f"QDialog{{background:{P['void']};}}")
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(12)

        title = QLabel("🔗  Get your MCP Link")
        title.setFont(QFont("Segoe UI",15,QFont.Bold))
        title.setStyleSheet(f"color:{P['mint']};background:transparent;")
        sub = QLabel("Login is only needed here — chat and tasks never require it.")
        sub.setFont(QFont("Segoe UI",9)); sub.setWordWrap(True)
        sub.setStyleSheet(f"color:{P['mid']};background:transparent;")
        lay.addWidget(title); lay.addWidget(sub)

        self._email = GlowInput("Email"); lay.addWidget(self._email)
        self._pw = GlowInput("Password"); self._pw.setEchoMode(QLineEdit.Password)
        lay.addWidget(self._pw)

        row = QHBoxLayout(); row.setSpacing(10)
        login_btn = PulseBtn("Log in", P["mint"], True)
        signup_btn = GhostBtn("Sign up", P["cyan"])
        login_btn.clicked.connect(self._do_login)
        signup_btn.clicked.connect(self._do_signup)
        row.addWidget(login_btn); row.addWidget(signup_btn)
        lay.addLayout(row)

        self._status = QLabel(""); self._status.setWordWrap(True)
        self._status.setFont(QFont("Segoe UI",9))
        self._status.setStyleSheet(f"color:{P['rose']};background:transparent;")
        lay.addWidget(self._status)

    def _do_login(self):
        try:
            self._mgr.log_in(self._email.text().strip(), self._pw.text())
            self.accept()
        except Exception as e:
            self._status.setText(str(e))

    def _do_signup(self):
        try:
            self._mgr.sign_up(self._email.text().strip(), self._pw.text())
            self.accept()
        except Exception as e:
            self._status.setText(str(e))

class Sidebar(QWidget):
    page_changed = Signal(int)

    def __init__(self,parent=None):
        super().__init__(parent); self.setFixedWidth(215)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._btns=[]
        self._link_mgr = None
        self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        lw=QWidget(); lw.setAttribute(Qt.WA_TranslucentBackground); lw.setFixedHeight(86)
        ll=QVBoxLayout(lw); ll.setContentsMargins(18,20,18,10); ll.setSpacing(3)
        lg=QLabel("⚙  NPM Agent"); lg.setFont(QFont("Segoe UI",14,QFont.Bold))
        lg.setStyleSheet(f"color:{P['mint']};background:transparent;")
        lv=QLabel("v4.0  ·  npmai_agents"); lv.setFont(QFont("Segoe UI",9))
        lv.setStyleSheet(f"color:{P['dim']};background:transparent;")
        ll.addWidget(lg); ll.addWidget(lv); lay.addWidget(lw)
        self._sep(lay)

        self._mcp_lbl=QLabel("  ● MCP Link: not connected")
        self._mcp_lbl.setFont(QFont("Segoe UI",9))
        self._mcp_lbl.setStyleSheet(f"color:{P['dim']};background:transparent;padding:6px 0;")
        lay.addWidget(self._mcp_lbl)
        self._sep(lay); lay.addSpacing(6)

        nl=QLabel("   NAVIGATION"); nl.setFont(QFont("Segoe UI",8,QFont.Bold))
        nl.setStyleSheet(f"color:{P['dim']};background:transparent;letter-spacing:3px;")
        lay.addWidget(nl); lay.addSpacing(2)

        for i in range(6):
            b=NavBtn(i); b.set_active(i==0)
            b.clicked.connect(self._on_nav)
            self._btns.append(b); lay.addWidget(b)

        lay.addStretch(); self._sep(lay)

        fw=QWidget(); fw.setAttribute(Qt.WA_TranslucentBackground)
        fl=QVBoxLayout(fw); fl.setContentsMargins(12,10,12,16); fl.setSpacing(8)

        self._mcp_btn=QPushButton("🔗  Get MCP Link")
        self._mcp_btn.setCursor(Qt.PointingHandCursor); self._mcp_btn.setFixedHeight(34)
        self._mcp_btn.setStyleSheet(self._btn_style())
        self._mcp_btn.clicked.connect(self._get_mcp_link)
        fl.addWidget(self._mcp_btn)

        for lbl,url in [("🐍 PyPI","https://pypi.org/project/npmai"),
                         ("⭐ GitHub","https://github.com/sonuramashishnpm")]:
            b2=QPushButton(lbl); b2.setCursor(Qt.PointingHandCursor); b2.setFixedHeight(32)
            b2.setStyleSheet(self._btn_style())
            import webbrowser
            b2.clicked.connect(lambda _,u=url: webbrowser.open(u))
            fl.addWidget(b2)

        eco=QLabel("Powered by NPMAI Ecosystem"); eco.setFont(QFont("Segoe UI",9))
        eco.setStyleSheet(f"color:{P['dim']};background:transparent;"); eco.setAlignment(Qt.AlignCenter)
        fl.addWidget(eco); lay.addWidget(fw)

    def _btn_style(self):
        return f"""QPushButton{{background:rgba(42,255,160,10);border:1px solid rgba(42,255,160,35);
border-radius:9px;color:{P['mid']};font-size:11px;font-family:'Segoe UI';}}
QPushButton:hover{{background:rgba(42,255,160,22);border-color:rgba(42,255,160,90);color:{P['mint']};}}"""

    def _sep(self,lay):
        s=QFrame(); s.setFixedHeight(1)
        s.setStyleSheet(f"background:{P['ghost']};border:none;"); lay.addWidget(s)

    def _on_nav(self,idx):
        for i,b in enumerate(self._btns): b.set_active(i==idx)
        self.page_changed.emit(idx)

    def _get_mcp_link(self):
        """ import here, not at module load time — mcp_link.py needs supabase """
        try:
            from mcp_link import MCPLinkManager, SupabaseAuthError
        except ImportError as e:
            QMessageBox.warning(self, "Missing dependency",
                f"MCP link needs the 'supabase' package.\nRun: pip install supabase\n\n{e}")
            return

        if self._link_mgr is None:
            self._link_mgr = MCPLinkManager(log_cb=lambda s: self._mcp_lbl.setText(f"  ● {s[:28]}"))

        if not self._link_mgr.is_logged_in:
            dlg = LoginDialog(self._link_mgr, self)
            if dlg.exec() != QDialog.Accepted:
                return

        try:
            link = self._link_mgr.get_or_create_link()
            self._link_mgr.start_listener()
            self._mcp_lbl.setText("  ● MCP Link: connected")
            self._mcp_lbl.setStyleSheet(f"color:{P['mint']};background:transparent;padding:6px 0;")
            QMessageBox.information(self, "Your MCP Link",
                f"Paste this into Claude/Grok's custom connector settings:\n\n{link}")
        except Exception as e:
            QMessageBox.warning(self, "Couldn't get MCP link", str(e))

    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        g=QLinearGradient(0,0,self.width(),0)
        g.setColorAt(0,QColor(6,4,18,245)); g.setColorAt(1,QColor(9,7,22,215))
        p.fillRect(self.rect(),QBrush(g))
        p.setPen(QPen(QColor(P["ghost"]),1))
        p.drawLine(self.width()-1,0,self.width()-1,self.height()); p.end()

class AgentPage(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._worker=None; self._killed=[False]
        self._build()

    def _build(self):
        outer=QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        topbar=QWidget(); topbar.setAttribute(Qt.WA_TranslucentBackground); topbar.setFixedHeight(64)
        tbl=QHBoxLayout(topbar); tbl.setContentsMargins(36,12,36,12); tbl.setSpacing(12)
        title=QLabel("NPM Agent"); title.setFont(QFont("Segoe UI",18,QFont.Bold))
        title.setStyleSheet(f"color:{P['mint']};background:transparent;")
        sub=QLabel("Runs fully locally · no login required"); sub.setFont(QFont("Segoe UI",10))
        sub.setStyleSheet(f"color:{P['dim']};background:transparent;")
        tc=QVBoxLayout(); tc.setSpacing(0); tc.addWidget(title); tc.addWidget(sub)
        tbl.addLayout(tc); tbl.addStretch()

        for badge,col in [("⚡ 100 Tools",P["mint"]),("🔒 Local-first",P["violet"]),("🤖 Agentic",P["cyan"])]:
            b=QLabel(f" {badge} "); b.setFont(QFont("Segoe UI",9,QFont.Bold))
            b.setStyleSheet(f"color:{col};background:rgba(42,255,160,12);border:1px solid rgba(42,255,160,35);border-radius:9px;padding:3px 8px;")
            tbl.addWidget(b)

        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{P['ghost']};border:none;")
        outer.addWidget(topbar); outer.addWidget(sep)
        chat_scroll=QScrollArea(); chat_scroll.setWidgetResizable(True)
        chat_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._chat_container=QWidget(); self._chat_container.setAttribute(Qt.WA_TranslucentBackground)
        self._chat_layout=QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(28,20,28,20); self._chat_layout.setSpacing(12)
        self._chat_layout.addStretch()
        chat_scroll.setWidget(self._chat_container)
        self._chat_scroll=chat_scroll
        outer.addWidget(chat_scroll,1)
        bottom=QWidget(); bottom.setAttribute(Qt.WA_TranslucentBackground)
        bl=QVBoxLayout(bottom); bl.setContentsMargins(28,14,28,20); bl.setSpacing(10)
        prow=QHBoxLayout(); prow.setSpacing(10)
        self._status_lbl=QLabel("Ready"); self._status_lbl.setFont(QFont("Segoe UI",10))
        self._status_lbl.setStyleSheet(f"color:{P['mid']};background:transparent;")
        self._pct_lbl=QLabel(""); self._pct_lbl.setFont(QFont("Segoe UI",10,QFont.Bold))
        self._pct_lbl.setStyleSheet(f"color:{P['mint']};background:transparent;")
        prow.addWidget(self._status_lbl); prow.addStretch(); prow.addWidget(self._pct_lbl)
        bl.addLayout(prow)
        self._prog=GlowProgress(); bl.addWidget(self._prog)
        self._log_box=QTextEdit(); self._log_box.setReadOnly(True)
        self._log_box.setFont(QFont("Cascadia Code",10))
        self._log_box.setFixedHeight(140)
        self._log_box.setStyleSheet(f"""QTextEdit{{background:rgba(4,3,12,190);
border:1px solid {P['ghost']};border-radius:11px;padding:10px;color:{P['bright']};}}""")
        self._log_box.setHtml(f'<font color="{P["dim"]}">Execution logs appear here…</font>')
        bl.addWidget(self._log_box)
        irow=QHBoxLayout(); irow.setSpacing(10)
        self._input=GlowInput("Ask anything or describe a task to automate…")
        self._input.returnPressed.connect(self._send)
        self._run_btn=PulseBtn("▶  Run",P["mint"]); self._run_btn.setFixedWidth(100)
        self._run_btn.clicked.connect(self._send)
        self._kill_btn=GhostBtn("■ Kill",P["rose"]); self._kill_btn.setFixedWidth(90)
        self._kill_btn.clicked.connect(self._kill); self._kill_btn.setEnabled(False)
        self._voice_btn=GhostBtn("🎤",P["sky"]); self._voice_btn.setFixedWidth(60)
        self._voice_btn.clicked.connect(self._voice_input)
        irow.addWidget(self._input); irow.addWidget(self._run_btn)
        irow.addWidget(self._kill_btn); irow.addWidget(self._voice_btn)
        bl.addLayout(irow)
        chips=QHBoxLayout(); chips.setSpacing(8)
        self._chip_tasks=[
            ("📁 Rename files","Rename all files in Downloads adding today's date prefix"),
            ("🌐 Scrape web","Scrape top 20 headlines from https://news.ycombinator.com save to news.xlsx on Desktop"),
            ("⭐ GitHub issue","Create a GitHub issue titled 'test' in my repo"),
            ("☁ AWS S3","List all objects in my S3 bucket"),
            ("🔒 Zip files","Find all PDFs in Documents sort by date zip into archive.zip on Desktop"),
            ("🖼 Resize imgs","Resize all images in Desktop/Photos folder to 800x600"),
        ]
        for label,task in self._chip_tasks:
            c=QPushButton(label); c.setCursor(Qt.PointingHandCursor); c.setFixedHeight(30)
            c.setStyleSheet(f"""QPushButton{{background:rgba(42,255,160,10);
border:1px solid rgba(42,255,160,38);border-radius:9px;
color:rgba(42,255,160,180);font-size:10px;padding:0 12px;}}
QPushButton:hover{{background:rgba(42,255,160,22);border-color:rgba(42,255,160,100);color:{P['mint']};}}""")
            c.clicked.connect(lambda _,t=task: self._input.setText(t))
            chips.addWidget(c)
        chips.addStretch(); bl.addLayout(chips)
        sep2=QFrame(); sep2.setFixedHeight(1); sep2.setStyleSheet(f"background:{P['ghost']};border:none;")
        outer.addWidget(sep2); outer.addWidget(bottom)

    def _add_bubble(self, text:str, is_agent:bool):
        b=ChatBubble(text, is_agent)
        self._chat_layout.insertWidget(self._chat_layout.count()-1, b)
        QTimer.singleShot(50, lambda: self._chat_scroll.verticalScrollBar().setValue(
            self._chat_scroll.verticalScrollBar().maximum()))

    def _log(self, html:str):
        self._log_box.append(html)
        self._log_box.verticalScrollBar().setValue(self._log_box.verticalScrollBar().maximum())

    def _voice_input(self):
        """ If you are working with voice input kindly read the documentation of npmai_agents and this code uses
        npmai_agents version 1.0.2, npmai_agents change frequently although not syntax but it will be better to read 
        before making any change."""
        """ old VoiceTool.listen(): SpeechAITool.transcribe_realtime """
        from npmai_agents.Tools_security_ai import SpeechAITool
        r = SpeechAITool.transcribe_realtime(duration=5)
        if r.success and r.data:
            self._input.setText(r.data.get("text",""))

    def _kill(self):
        if self._worker: self._worker.kill()
        self._kill_btn.setEnabled(False)
        self._run_btn.setEnabled(True); self._run_btn.setText("▶  Run")

    def _send(self):
        task=self._input.text().strip()
        if not task: return
        self._input.clear()
        self._add_bubble(task, False)
        self._run_btn.setEnabled(False); self._run_btn.setText("⏳")
        self._kill_btn.setEnabled(True)
        self._prog.set_value(3)
        self._log_box.clear()
        self._worker=AgentWorker(task)
        self._worker.log_sig.connect(self._log)
        self._worker.progress_sig.connect(self._prog.set_value)
        self._worker.progress_sig.connect(lambda v: self._pct_lbl.setText(f"{v}%"))
        self._worker.status_sig.connect(lambda s: self._status_lbl.setText(s))
        self._worker.bubble_sig.connect(self._add_bubble)
        self._worker.done_sig.connect(self._done)
        self._worker.start()

    def _done(self, ok:bool, msg:str):
        self._run_btn.setEnabled(True); self._run_btn.setText("▶  Run")
        self._kill_btn.setEnabled(False)
        self._status_lbl.setText("Done ✓" if ok else "Failed")


class HistoryPage(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.setAttribute(Qt.WA_TranslucentBackground); self._build()

    def _build(self):
        outer=QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        page=QWidget(); page.setAttribute(Qt.WA_TranslucentBackground)
        self._lay=QVBoxLayout(page); self._lay.setContentsMargins(36,36,36,36); self._lay.setSpacing(10)
        header=QHBoxLayout()
        t=QLabel("📋  Task History"); t.setFont(QFont("Segoe UI",20,QFont.Bold))
        t.setStyleSheet(f"color:{P['cyan']};background:transparent;")
        refresh=GhostBtn("↺ Refresh",P["cyan"]); refresh.setFixedSize(110,36)
        refresh.clicked.connect(self.load)
        header.addWidget(t); header.addStretch(); header.addWidget(refresh)
        self._lay.addLayout(header)
        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{P['ghost']};border:none;")
        self._lay.addWidget(sep); self._lay.addSpacing(10)
        self._items_layout=QVBoxLayout(); self._lay.addLayout(self._items_layout)
        self._lay.addStretch()
        scroll.setWidget(page); outer.addWidget(scroll)
        self.load()

    def load(self):
        while self._items_layout.count():
            item=self._items_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        history=AgentBrain.load_task_history()
        if not history:
            lbl=QLabel("No tasks run yet. Go to Agent tab and run your first task!")
            lbl.setFont(QFont("Segoe UI",12)); lbl.setStyleSheet(f"color:{P['mid']};background:transparent;")
            self._items_layout.addWidget(lbl); return
        for entry in history:
            row=GlowCard(accent=P["mint"] if entry["success"] else P["rose"],radius=14,alpha=190)
            row.setFixedHeight(70)
            rl=QHBoxLayout(row); rl.setContentsMargins(20,12,20,12); rl.setSpacing(14)
            dot=QLabel("✓" if entry["success"] else "✗")
            dot.setFont(QFont("Segoe UI",14,QFont.Bold))
            dot.setStyleSheet(f"color:{P['mint'] if entry['success'] else P['rose']};background:transparent;")
            dot.setFixedWidth(22)
            tc=QVBoxLayout(); tc.setSpacing(2)
            task_lbl=QLabel(entry["task"][:80]+("…" if len(entry["task"])>80 else ""))
            task_lbl.setFont(QFont("Segoe UI",11))
            task_lbl.setStyleSheet(f"color:{P['bright']};background:transparent;")
            time_lbl=QLabel(entry["time"][:19].replace("T"," "))
            time_lbl.setFont(QFont("Segoe UI",9))
            time_lbl.setStyleSheet(f"color:{P['dim']};background:transparent;")
            tc.addWidget(task_lbl); tc.addWidget(time_lbl)
            rl.addWidget(dot); rl.addLayout(tc); rl.addStretch()
            self._items_layout.addWidget(row)


def _discover_real_tools():
    import npmai_agents as pkg
    tools = []
    for attr_name in dir(pkg):
        obj = getattr(pkg, attr_name)
        if isinstance(obj, type) and hasattr(obj, "name") and hasattr(obj, "description"):
            tools.append((getattr(obj, "name"), attr_name, getattr(obj, "description")))
    return sorted(tools, key=lambda t: t[1])


class ToolsPage(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.setAttribute(Qt.WA_TranslucentBackground); self._build()

    def _build(self):
        outer=QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        page=QWidget(); page.setAttribute(Qt.WA_TranslucentBackground)
        lay=QVBoxLayout(page); lay.setContentsMargins(36,36,36,36); lay.setSpacing(20)

        tools = _discover_real_tools()
        t=QLabel(f"🛠  Tool Registry — {len(tools)} Integrated Tools")
        t.setFont(QFont("Segoe UI",20,QFont.Bold))
        t.setStyleSheet(f"color:{P['amber']};background:transparent;")
        lay.addWidget(t)
        desc=QLabel("Read directly from npmai_agents — always matches what's actually installed. "
                     "All tools are available to the agent automatically; just describe your task.")
        desc.setFont(QFont("Segoe UI",11)); desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{P['mid']};background:transparent;")
        lay.addWidget(desc)
        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{P['ghost']};border:none;")
        lay.addWidget(sep); lay.addSpacing(6)

        cols_palette = [P["mint"],P["cyan"],P["violet"],P["amber"],P["sky"],P["rose"]]
        grid_cols = 2
        grid_row = None
        for i, (tool_name, cls_name, description) in enumerate(tools):
            if i % grid_cols == 0:
                grid_row = QHBoxLayout(); grid_row.setSpacing(16); lay.addLayout(grid_row)
            col = cols_palette[i % len(cols_palette)]
            card=GlowCard(accent=col,radius=16,alpha=195); card.setFixedHeight(108)
            cl=QHBoxLayout(card); cl.setContentsMargins(20,16,20,16); cl.setSpacing(14)
            cv=QVBoxLayout(); cv.setSpacing(4)
            n=QLabel(cls_name); n.setFont(QFont("Segoe UI",13,QFont.Bold))
            n.setStyleSheet(f"color:{P['bright']};background:transparent;")
            c2=QLabel(tool_name); c2.setFont(QFont("Cascadia Code",9))
            c2.setStyleSheet(f"color:{col};background:transparent;")
            d=QLabel(description[:140]+("…" if len(description)>140 else ""))
            d.setFont(QFont("Segoe UI",10)); d.setWordWrap(True)
            d.setStyleSheet(f"color:{P['mid']};background:transparent;")
            cv.addWidget(n); cv.addWidget(c2); cv.addWidget(d)
            cl.addLayout(cv)
            grid_row.addWidget(card)
        if len(tools) % grid_cols != 0 and grid_row is not None:
            grid_row.addStretch()

        lay.addStretch()
        scroll.setWidget(page); outer.addWidget(scroll)


class SettingsPage(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.setAttribute(Qt.WA_TranslucentBackground); self._build()

    def _section(self, lay, title, fields, cred_key, accent):
        card=GlowCard(accent=accent,radius=18,alpha=200)
        cl=QVBoxLayout(card); cl.setContentsMargins(28,22,28,22); cl.setSpacing(14)
        h=QLabel(title); h.setFont(QFont("Segoe UI",13,QFont.Bold))
        h.setStyleSheet(f"color:{P['bright']};background:transparent;"); cl.addWidget(h)
        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{P['ghost']};border:none;")
        cl.addWidget(sep)
        inputs={}
        for field_key,label,placeholder,is_pw in fields:
            lbl=QLabel(label); lbl.setFont(QFont("Segoe UI",10))
            lbl.setStyleSheet(f"color:{P['mid']};background:transparent;"); cl.addWidget(lbl)
            inp=GlowInput(placeholder)
            if is_pw: inp.setEchoMode(QLineEdit.Password)
            existing=CredStore.load(cred_key).get(field_key,"")
            if existing: inp.setText("●"*8 if is_pw else existing)
            inputs[field_key]=inp; cl.addWidget(inp)
        save_btn=PulseBtn(f"💾  Save {title.split()[0]} Credentials",accent,True)
        save_btn.setFixedHeight(42)
        def _save(ck=cred_key,inp_ref=inputs):
            data={}
            for k,w in inp_ref.items():
                v=w.text().strip()
                if v and v!="●"*8: data[k]=v
            existing=CredStore.load(ck)
            existing.update(data); CredStore.save(ck,existing)
            QMessageBox.information(self,"Saved",f"{ck} credentials saved securely.")
        save_btn.clicked.connect(_save); cl.addWidget(save_btn)
        lay.addWidget(card)

    def _build(self):
        outer=QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        page=QWidget(); page.setAttribute(Qt.WA_TranslucentBackground)
        lay=QVBoxLayout(page); lay.setContentsMargins(36,36,36,36); lay.setSpacing(20)
        t=QLabel("⚙  Settings & Credentials"); t.setFont(QFont("Segoe UI",20,QFont.Bold))
        t.setStyleSheet(f"color:{P['violet']};background:transparent;"); lay.addWidget(t)
        sub=QLabel("All credentials are encrypted with a machine-specific key (CredStore) and stored "
                    "locally. Never sent anywhere. No login needed for anything on this page.")
        sub.setFont(QFont("Segoe UI",10)); sub.setWordWrap(True)
        sub.setStyleSheet(f"color:{P['mid']};background:transparent;"); lay.addWidget(sub)
        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{P['ghost']};border:none;")
        lay.addWidget(sep); lay.addSpacing(6)

        ws_card=GlowCard(accent=P["cyan"],radius=16,alpha=195)
        wl=QHBoxLayout(ws_card); wl.setContentsMargins(24,16,24,16); wl.setSpacing(16)
        wl_v=QVBoxLayout(); wl_v.setSpacing(4)
        wl_t=QLabel("🖥  Workspace Scanner"); wl_t.setFont(QFont("Segoe UI",13,QFont.Bold))
        wl_t.setStyleSheet(f"color:{P['bright']};background:transparent;")
        wl_d=QLabel("Scans your Desktop, Downloads, Documents, Pictures, Videos, Music — agent uses this to understand your file system")
        wl_d.setFont(QFont("Segoe UI",10)); wl_d.setWordWrap(True)
        wl_d.setStyleSheet(f"color:{P['mid']};background:transparent;")
        wl_v.addWidget(wl_t); wl_v.addWidget(wl_d)
        scan_btn=PulseBtn("🔍  Scan Now",P["cyan"],True); scan_btn.setFixedSize(130,38)
        def _scan():
            ws=Workspace(); ws.scan()
            QMessageBox.information(self,"Scanned","Workspace scanned successfully!")
        scan_btn.clicked.connect(_scan); wl.addLayout(wl_v); wl.addStretch(); wl.addWidget(scan_btn)
        lay.addWidget(ws_card)

        # ── Credential sections — cred_key + fields verified against source ──
        self._section(lay,"⭐ GitHub",[
            ("token","Personal access token (repo + issues scope)","ghp_xxxxxxxxxxxx",True),
        ],"github",P["cyan"])

        self._section(lay,"📧 Email (SMTP)",[
            ("email","Email address","your@gmail.com",False),
            ("password","App password","Gmail app password",True),
            ("smtp_host","SMTP host","smtp.gmail.com",False),
            ("smtp_port","SMTP port","587",False),
        ],"smtp",P["mint"])

        self._section(lay,"📓 Notion",[
            ("token","Integration token","secret_xxxxxxxxxxxx",True),
        ],"notion",P["amber"])

        self._section(lay,"💳 Stripe",[
            ("secret_key","Secret key","sk_live_xxxxxxxxxxxx",True),
        ],"stripe",P["violet"])

        self._section(lay,"☁ AWS",[
            ("access_key_id","Access key ID","AKIA...",False),
            ("secret_access_key","Secret access key","",True),
            ("region","Region","us-east-1",False),
        ],"aws",P["sky"])

        note=QLabel("More tools follow the same pattern — CredStore.save('<cred_key>', {...}). "
                     "Check each tool's `use` docstring (visible to the agent's Coder role) for its "
                     "exact cred_key and field names before wiring up a new section here.")
        note.setFont(QFont("Segoe UI",9)); note.setWordWrap(True)
        note.setStyleSheet(f"color:{P['dim']};background:transparent;"); lay.addWidget(note)

        mcp_card=GlowCard(accent=P["mint"],radius=16,alpha=195)
        ml=QVBoxLayout(mcp_card); ml.setContentsMargins(24,18,24,18); ml.setSpacing(8)
        mt=QLabel("🔗  MCP Link"); mt.setFont(QFont("Segoe UI",13,QFont.Bold))
        mt.setStyleSheet(f"color:{P['bright']};background:transparent;"); ml.addWidget(mt)
        md=QLabel(
            "Click 'Get MCP Link' in the sidebar to log in and receive your personal link. "
            "Paste it into Claude/Grok's custom connector settings — this app then executes "
            "already-audited code sent by the hosted MCP server and reports results back.\n"
            "This is the ONLY feature in the app that requires login."
        )
        md.setFont(QFont("Segoe UI",10)); md.setWordWrap(True)
        md.setStyleSheet(f"color:{P['mid']};background:transparent;"); ml.addWidget(md)
        lay.addWidget(mcp_card)
        lay.addStretch(); scroll.setWidget(page); outer.addWidget(scroll)


class FounderPage(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.setAttribute(Qt.WA_TranslucentBackground); self._build()

    def _build(self):
        outer=QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        page=QWidget(); page.setAttribute(Qt.WA_TranslucentBackground)
        lay=QVBoxLayout(page); lay.setContentsMargins(36,36,36,36); lay.setSpacing(20)

        import webbrowser
        t=QLabel("👤  The Founder"); t.setFont(QFont("Segoe UI",20,QFont.Bold))
        t.setStyleSheet(f"color:{P['violet']};background:transparent;"); lay.addWidget(t)
        hero=GlowCard(accent=P["violet"],radius=22,alpha=210)
        hl=QVBoxLayout(hero); hl.setContentsMargins(32,28,32,28); hl.setSpacing(14)
        name=QLabel("Sonu Kumar  🇮🇳"); name.setFont(QFont("Segoe UI",22,QFont.Bold))
        name.setStyleSheet(f"color:{P['bright']};background:transparent;"); hl.addWidget(name)
        tag=QLabel("Founder · NPMAI ECOSYSTEM · Bihar Viral Boy")
        tag.setFont(QFont("Segoe UI",12)); tag.setStyleSheet(f"color:{P['violet']};background:transparent;")
        hl.addWidget(tag)
        links=QHBoxLayout(); links.setSpacing(10)
        for lbl2,url in [("⭐ GitHub","https://github.com/sonuramashishnpm"),
                          ("🐍 PyPI","https://pypi.org/project/npmai")]:
            b2=QPushButton(lbl2); b2.setCursor(Qt.PointingHandCursor); b2.setFixedHeight(32)
            b2.setStyleSheet(f"QPushButton{{background:rgba(167,139,250,10);border:1px solid rgba(167,139,250,40);border-radius:9px;color:{P['mid']};font-size:11px;padding:0 12px;}}QPushButton:hover{{background:rgba(167,139,250,25);border-color:rgba(167,139,250,110);color:{P['bright']};}}")
            b2.clicked.connect(lambda _,u=url: webbrowser.open(u)); links.addWidget(b2)
        links.addStretch(); hl.addLayout(links); lay.addWidget(hero)
        lay.addStretch(); scroll.setWidget(page); outer.addWidget(scroll)


class DocsPage(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.setAttribute(Qt.WA_TranslucentBackground); self._build()

    def _sec(self,lay,icon,title,col,items):
        card=GlowCard(accent=col,radius=18,alpha=195)
        cl=QVBoxLayout(card); cl.setContentsMargins(28,22,28,22); cl.setSpacing(14)
        h=QHBoxLayout()
        ic=QLabel(icon); ic.setFont(QFont("Segoe UI",16)); ic.setStyleSheet("background:transparent;"); ic.setFixedWidth(28)
        tt=QLabel(title); tt.setFont(QFont("Segoe UI",13,QFont.Bold))
        tt.setStyleSheet(f"color:{P['bright']};background:transparent;")
        h.addWidget(ic); h.addWidget(tt); h.addStretch(); cl.addLayout(h)
        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{P['ghost']};border:none;")
        cl.addWidget(sep)
        for it,ib in items:
            row=QHBoxLayout(); row.setSpacing(12)
            dot=QLabel("▸"); dot.setFont(QFont("Segoe UI",11,QFont.Bold))
            dot.setStyleSheet(f"color:{col};background:transparent;"); dot.setFixedWidth(16); dot.setAlignment(Qt.AlignTop)
            cv=QVBoxLayout(); cv.setSpacing(1)
            it_l=QLabel(it); it_l.setFont(QFont("Segoe UI",11,QFont.Bold))
            it_l.setStyleSheet(f"color:{P['bright']};background:transparent;")
            ib_l=QLabel(ib); ib_l.setFont(QFont("Segoe UI",11)); ib_l.setWordWrap(True)
            ib_l.setStyleSheet(f"color:{P['mid']};background:transparent;")
            cv.addWidget(it_l); cv.addWidget(ib_l)
            row.addWidget(dot); row.addLayout(cv); cl.addLayout(row)
        lay.addWidget(card)

    def _build(self):
        outer=QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        page=QWidget(); page.setAttribute(Qt.WA_TranslucentBackground)
        lay=QVBoxLayout(page); lay.setContentsMargins(36,36,36,36); lay.setSpacing(20)

        t=QLabel("📖  Documentation"); t.setFont(QFont("Segoe UI",20,QFont.Bold))
        t.setStyleSheet(f"color:{P['sky']};background:transparent;"); lay.addWidget(t)
        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{P['ghost']};border:none;")
        lay.addWidget(sep); lay.addSpacing(4)

        self._sec(lay,"🚀","Getting Started",P["mint"],[
            ("Install","pip install npmai_agents, then run this app."),
            ("First scan","Go to Settings and click 'Scan Now' — agent learns your folder structure."),
            ("Add credentials","Add GitHub/Notion/Stripe/AWS/SMTP creds in Settings. Encrypted locally."),
            ("Type a task","In the Agent tab, describe any task in plain English and press Run. No login needed."),
        ])
        self._sec(lay,"🤖","How the Agent Works (Standalone)",P["cyan"],[
            ("Detect intent","Local heuristic decides: conversation, or a task to execute?"),
            ("Plan","Planner LLM breaks the task into atomic steps."),
            ("Select tools","Tool Manager picks from the real 100-tool registry."),
            ("Generate","Coder LLM writes Python for each step."),
            ("Audit","Auditor LLM reviews the code before anything runs."),
            ("Execute","Executor runs it as a real child process — streams to the log panel."),
            ("Verify","Verifier LLM confirms the step actually completed."),
            ("Retry","On failure, agent auto-debugs up to 12 times with prior error context."),
        ])
        self._sec(lay,"🔗","MCP Link (opt-in, login required)",P["violet"],[
            ("Get a link","Sidebar → 'Get MCP Link' → log in (or sign up) → link issued for your account."),
            ("Connect","Paste the link into Claude/Grok's custom connector settings."),
            ("What runs here","Only the execution step — the LLM you connected does the planning/coding, "
                              "already audited before it reaches this app."),
            ("Everything else stays local","Chat, tasks, and credentials never touch this — login is scoped "
                              "to this one feature only."),
        ])
        self._sec(lay,"🔒","Security",P["rose"],[
            ("Dual-role audit","Every script is reviewed by a separate Auditor role before execution."),
            ("Subprocess isolation","Code runs as a child process — a broken script cannot crash the app."),
            ("Kill button","Click ■ Kill at any time to terminate the running script immediately."),
            ("Credential encryption","Fernet symmetric encryption, machine-specific key, local only. Never uploaded."),
        ])
        lay.addStretch(); scroll.setWidget(page); outer.addWidget(scroll)


class AppWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NPM Agent  —  NPMAI Ecosystem  v4.0")
        self.resize(1220,780); self.setMinimumSize(920,640)
        self._build()

    def _build(self):
        self.bg=CosmicBG(self); self.bg.lower()
        root=QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.sidebar=Sidebar(); self.sidebar.page_changed.connect(self._switch)
        root.addWidget(self.sidebar)
        content=QWidget(); content.setAttribute(Qt.WA_TranslucentBackground)
        cl=QVBoxLayout(content); cl.setContentsMargins(0,0,0,0)
        self.stack=QStackedWidget(); self.stack.setAttribute(Qt.WA_TranslucentBackground)
        self.stack.setStyleSheet("background:transparent;")
        self.stack.addWidget(AgentPage())
        self.stack.addWidget(HistoryPage())
        self.stack.addWidget(ToolsPage())
        self.stack.addWidget(SettingsPage())
        self.stack.addWidget(FounderPage())
        self.stack.addWidget(DocsPage())
        cl.addWidget(self.stack); root.addWidget(content)

    def resizeEvent(self,e):
        super().resizeEvent(e); self.bg.setGeometry(0,0,self.width(),self.height())

    def _switch(self,idx):
        if idx==1:
            self.stack.widget(1).load()
        widget=self.stack.widget(idx)
        eff=QGraphicsOpacityEffect(widget); widget.setGraphicsEffect(eff)
        anim=QPropertyAnimation(eff,b"opacity",self)
        anim.setDuration(280); anim.setStartValue(0); anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        self.stack.setCurrentIndex(idx); anim.start()
        self._anim=anim

    def closeEvent(self,e):
        if hasattr(self.sidebar, "_link_mgr") and self.sidebar._link_mgr:
            self.sidebar._link_mgr.stop_listener()
        super().closeEvent(e)


if __name__=="__main__":
    app=QApplication(sys.argv); app.setStyle("Fusion")
    pal=QPalette()
    pal.setColor(QPalette.Window,           QColor(P["void"]))
    pal.setColor(QPalette.WindowText,       QColor(P["bright"]))
    pal.setColor(QPalette.Base,             QColor(P["deep"]))
    pal.setColor(QPalette.AlternateBase,    QColor(P["panel"]))
    pal.setColor(QPalette.Text,             QColor(P["bright"]))
    pal.setColor(QPalette.Button,           QColor(P["lift"]))
    pal.setColor(QPalette.ButtonText,       QColor(P["bright"]))
    pal.setColor(QPalette.Highlight,        QColor(P["mint"]))
    pal.setColor(QPalette.HighlightedText,  QColor("#050310"))
    app.setPalette(pal)
    win=AppWindow(); win.show(); sys.exit(app.exec())
