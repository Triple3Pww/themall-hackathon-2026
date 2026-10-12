"""Edit the No Cap pitch deck: add Visual Mockup, Implementation Plan and Future-Ready slides,
swap the CO/PM2.5 KPI for carbon saved, renumber kickers and footers.

Run from TheMall/slides:  python3 build_deck.py
Input:  unpacked/ (extracted No_Cap_Pitch_Deck_original.pptx), mock-driver.png, mock-wide.png
Output: No_Cap_Pitch_Deck.pptx
"""
import os
import re
import shutil
import zipfile
from xml.sax.saxutils import escape

U = "unpacked"
SL = f"{U}/ppt/slides"
NAVY, INK, MUTE, FOOT = "1B2A41", "1B2A41", "5C6B7A", "8FA0AF"
GREEN, AMBER, GREEN_TXT, AMBER_TXT = "00C896", "FFB020", "00A87D", "E09A00"
CARD_TINT = "E8EDF2"

FONT = ('<a:latin typeface="Loma" pitchFamily="34" charset="0"/>'
        '<a:ea typeface="Loma" pitchFamily="34" charset="-122"/>'
        '<a:cs typeface="Loma" pitchFamily="34" charset="-120"/>')


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


# ---------------------------------------------------------------- shape builders
class Slide:
    def __init__(self):
        self.shapes, self.n = [], 1

    def nid(self):
        self.n += 1
        return self.n

    def rect(self, x, y, w, h, fill, rounded=True, shadow=True, geom=None):
        i = self.nid()
        g = geom or ("roundRect" if rounded else "rect")
        av = '<a:gd name="adj" fmla="val 1978"/>' if g == "roundRect" else ""
        sh = ('<a:effectLst> <a:outerShdw sx="100000" sy="100000" kx="0" ky="0" algn="bl" rotWithShape="0" '
              'blurRad="101600" dist="38100" dir="5400000"> <a:srgbClr val="1B2A41"> <a:alpha val="12000"/></a:srgbClr> '
              '</a:outerShdw></a:effectLst>') if shadow else ""
        self.shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="Shape {i}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="{g}"><a:avLst>{av}</a:avLst></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill><a:ln/>{sh}</p:spPr></p:sp>')

    def text(self, x, y, w, h, paras, anchor="t"):
        """paras: list of dicts {t, sz, b, i, color, bullet, align, after}"""
        i = self.nid()
        ps = []
        for p in paras:
            sz = p.get("sz", 1350)
            if p.get("bullet"):
                ppr = (f'<a:pPr marL="228600" indent="-228600"><a:lnSpc><a:spcPct val="112000"/></a:lnSpc>'
                       f'<a:spcAft><a:spcPts val="{p.get("after", 1000)}"/></a:spcAft><a:buSzPct val="100000"/><a:buChar char="&#x25AA;"/></a:pPr>')
            else:
                al = f' algn="{p["align"]}"' if p.get("align") else ""
                ppr = (f'<a:pPr{al} indent="0" marL="0"><a:lnSpc><a:spcPct val="108000"/></a:lnSpc>'
                       f'<a:spcAft><a:spcPts val="{p.get("after", 0)}"/></a:spcAft><a:buNone/></a:pPr>')
            attrs = f'lang="th-TH" sz="{sz}"' + (' b="1"' if p.get("b") else "") + (' i="1"' if p.get("i") else "")
            ps.append(f'<a:p>{ppr}<a:r><a:rPr {attrs} dirty="0"><a:solidFill><a:srgbClr val="{p.get("color", INK)}"/></a:solidFill>'
                      f'{FONT}</a:rPr><a:t>{escape(p["t"])}</a:t></a:r><a:endParaRPr lang="th-TH" sz="{sz}" dirty="0"/></a:p>')
        self.shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="Text {i}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln/></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" rtlCol="0" anchor="{anchor}"/><a:lstStyle/>{"".join(ps)}</p:txBody></p:sp>')

    def pic(self, rid, x, y, w, h, descr):
        i = self.nid()
        self.shapes.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{i}" name="Image {i}" descr="{escape(descr)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 3000"/></a:avLst></a:prstGeom></p:spPr></p:pic>')


def header(s, circle, kicker, kcolor, title, subtitle):
    """Same header as the existing content slides; the icon picture is always rId1."""
    s.rect(10929823, 475488, 713232, 713232, circle, shadow=False, geom="ellipse")
    s.pic("rId1", 11100999, 646664, 370881, 370881, "icon")
    s.shapes[-1] = s.shapes[-1].replace('<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 3000"/></a:avLst></a:prstGeom>',
                                        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>')
    i = s.nid()
    s.shapes.append(
        f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="Kicker"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="548640" y="502920"/>'
        f'<a:ext cx="7772400" cy="292608"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln/></p:spPr><p:txBody>'
        f'<a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" rtlCol="0" anchor="ctr"/><a:lstStyle/><a:p><a:pPr indent="0" marL="0"><a:buNone/></a:pPr>'
        f'<a:r><a:rPr lang="en-US" sz="1200" b="1" spc="200" kern="0" dirty="0"><a:solidFill><a:srgbClr val="{kcolor}"/></a:solidFill>{FONT}</a:rPr>'
        f'<a:t>{escape(kicker)}</a:t></a:r></a:p></p:txBody></p:sp>')
    s.text(548640, 804672, 8961120, 566928, [dict(t=title, sz=3000, b=True)], anchor="ctr")
    s.text(548640, 1389888, 8961120, 292608, [dict(t=subtitle, sz=1300, i=True, color=MUTE)], anchor="ctr")


def footer(s, page, total):
    s.text(548640, 6473952, 4572000, 274320, [dict(t="URGENT SUD SUD  ·  NO CAP", sz=900, color=FOOT)], anchor="ctr")
    s.text(10271455, 6473952, 1371600, 274320, [dict(t=f"{page:02d} / {total}", sz=900, color=FOOT, align="r")], anchor="ctr")


def slide_xml(s, name):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            f'<p:cSld name="{name}"><p:bg><p:bgPr><a:solidFill><a:srgbClr val="F5F7F9"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
            '<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            + "".join(s.shapes) +
            '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


# ---------------------------------------------------------------- content
TOTAL = 14
X0, CW, Y0, CH = 548640, 11064240, 1874520, 4160520   # content box used by the deck


def mockup_slide(page):
    s = Slide()
    header(s, GREEN, "04 · VISUAL MOCKUP", GREEN_TXT, "ภาพจำลองการทำงานจริง",
           "What the driver sees at the turn, and what the cameras count behind it")
    w = 5349240
    for k, (rid, ttl, body) in enumerate([
        ("rId2", "มุมมองคนขับ", "ป้ายบอกคำแนะนำตัวใหญ่ พร้อมจำนวนช่องที่เหลือจริงของชั้นนี้และชั้นบน วางไว้ก่อนถึงทางเลี้ยวเข้าชั้น"),
        ("rId3", "ภาพรวมทั้งชั้น", "ทางวนขึ้น–ลง กล้องนับรถ 2 ตัวที่ทางเข้า–ออกชั้น และเซนเซอร์ช่องจอดเดิม ทำงานร่วมกันเพื่อคำนวณตัวเลขบนป้าย"),
    ]):
        x = X0 + k * (w + 365760)
        s.rect(x, Y0, w, CH, "FFFFFF")
        iw = w - 2 * 182880
        ih = int(iw * 612 / 1040)
        s.pic(rid, x + 182880, Y0 + 182880, iw, ih, ttl)
        s.text(x + 182880, Y0 + 182880 + ih + 182880, iw, CH - ih - 3 * 182880,
               [dict(t=ttl, sz=1500, b=True, after=400), dict(t=body, sz=1200, color=MUTE)])
    footer(s, page, TOTAL)
    return s


def plan_slide(page):
    s = Slide()
    header(s, AMBER, "09 · IMPLEMENTATION PLAN", AMBER_TXT, "แผนการนำไปใช้จริง",
           "Install, measure a baseline, then switch one floor at a time")
    steps = [
        ("ติดตั้งและเชื่อมข้อมูล", "ติดกล้องนับรถ 2 ตัวต่อชั้นเหนือทางลาด หรือใช้ CCTV เดิม แล้วดึงข้อมูลจากเซนเซอร์ช่องจอดที่มีอยู่"),
        ("เก็บ baseline 2 สัปดาห์", "ระบบนับและคำนวณทุกอย่าง แต่ยังไม่เปลี่ยนป้าย เพื่อรู้ค่าเริ่มต้นของเวลาหาที่จอด"),
        ("เปิดป้ายใหม่ทีละชั้น", "เปิดป้ายใหม่ 1 ชั้น อีกชั้นใช้ป้ายเดิม แล้วสลับชั้นกันในสัปดาห์ถัดไป เพื่อเทียบอย่างเป็นธรรม"),
        ("ประเมินผลและขยาย", "เทียบ KPI กับ baseline พร้อมรายงานจำนวนรถทั้งหมดคู่กัน ถ้าผ่านเกณฑ์จึงขยายทุกชั้น"),
    ]
    gap = 274320
    w = (CW - 3 * gap) // 4
    h = 2377440
    colors = [GREEN, AMBER, GREEN, AMBER]
    for k, (ttl, body) in enumerate(steps):
        x = X0 + k * (w + gap)
        s.rect(x, Y0, w, h, "FFFFFF")
        s.rect(x + 228600, Y0 + 228600, 502920, 502920, colors[k], shadow=False, geom="ellipse")
        s.text(x + 228600, Y0 + 228600, 502920, 502920, [dict(t=str(k + 1), sz=1800, b=True, color=NAVY, align="ctr")], anchor="ctr")
        s.text(x + 228600, Y0 + 868680, w - 457200, 1371600,
               [dict(t=ttl, sz=1500, b=True, after=600), dict(t=body, sz=1200, color=MUTE)])
    by = Y0 + h + gap
    s.rect(X0, by, CW, Y0 + CH - by, "FFFFFF")
    s.text(X0 + 320040, by + 228600, CW - 640080, 1371600, [
        dict(t="เกณฑ์ก่อนขยายผล", sz=1500, b=True, after=800),
        dict(t="เวลาหาที่จอดเฉลี่ย (Little's Law) ลดลงเมื่อเทียบกับ baseline ของชั้นเดียวกัน", sz=1300, bullet=True, after=500),
        dict(t="จำนวนรถที่เข้ามาทั้งหมดไม่เพิ่มขึ้นผิดปกติ (guardrail) และป้ายไม่สลับคำแนะนำถี่เกินไป", sz=1300, bullet=True, after=0),
    ])
    footer(s, page, TOTAL)
    return s


def future_slide(page):
    s = Slide()
    header(s, NAVY, "12 · FUTURE-READY", GREEN_TXT, "ต่อยอดสู่อนาคต",
           "Same cameras, same subtraction: more places to use it")
    items = [
        ("แจ้งก่อนถึงห้าง", "ส่งตัวเลขเดียวกันเข้าแอปของศูนย์การค้าหรือจอที่ทางเข้า ให้คนขับเลือกชั้นได้ตั้งแต่ก่อนขึ้นทางวน"),
        ("ช่องจอดเฉพาะ เช่น ช่องชาร์จ EV", "ใช้วิธีลบกันแบบเดียวกันกับโซนชาร์จ EV หรือช่องจอดผู้พิการ เพื่อบอกว่าโซนไหนว่างจริง"),
        ("ข้อมูลให้ร้านค้าและการจัดคน", "การแย่งช่องจอดรายชั้นรายชั่วโมง บอกช่วงพีคของร้านหลัก และจุดที่ควรวางพนักงานจัดระเบียบรถ"),
        ("ขยายทุกสาขาด้วยซอฟต์แวร์เดียว", "สาขาที่มีเซนเซอร์ช่องจอดอยู่แล้ว เพิ่มแค่กล้องนับรถ แล้วใช้ซอฟต์แวร์ชุดเดียวกันได้ทันที"),
    ]
    gap = 274320
    w = (CW - gap) // 2
    h = (CH - gap) // 2
    for k, (ttl, body) in enumerate(items):
        x = X0 + (k % 2) * (w + gap)
        y = Y0 + (k // 2) * (h + gap)
        s.rect(x, y, w, h, "FFFFFF")
        s.text(x + 320040, y + 274320, w - 640080, h - 548640,
               [dict(t=ttl, sz=1500, b=True, after=700), dict(t=body, sz=1300, color=MUTE)])
    footer(s, page, TOTAL)
    return s


# ---------------------------------------------------------------- package edits
def add_slide(num, slide, icon_media, images=()):
    """Register slide{num}.xml with an icon (rId1), extra images (rId2..), and the content layout."""
    write(f"{SL}/slide{num}.xml", slide_xml(slide, f"Slide {num}"))
    rels = [f'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{icon_media}"/>']
    for k, img in enumerate(images, start=2):
        rels.append(f'<Relationship Id="rId{k}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{img}"/>')
    rels.append(f'<Relationship Id="rId{len(images) + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>')
    write(f"{SL}/_rels/slide{num}.xml.rels",
          '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
          + "".join(rels) + "</Relationships>")
    ct = read(f"{U}/[Content_Types].xml")
    part = f'/ppt/slides/slide{num}.xml'
    if part not in ct:
        ct = ct.replace("</Types>", f'<Override PartName="{part}" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>')
        write(f"{U}/[Content_Types].xml", ct)
    prels = read(f"{U}/ppt/_rels/presentation.xml.rels")
    m = re.search(rf'Id="(rId\d+)"[^>]*Target="slides/slide{num}.xml"', prels)
    if m:
        return m.group(1)
    nxt = max(int(n) for n in re.findall(r'Id="rId(\d+)"', prels)) + 1
    prels = prels.replace("</Relationships>", f'<Relationship Id="rId{nxt}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{num}.xml"/></Relationships>')
    write(f"{U}/ppt/_rels/presentation.xml.rels", prels)
    return f"rId{nxt}"


def main():
    shutil.copy("mock-driver.png", f"{U}/ppt/media/mock-driver.png")
    shutil.copy("mock-wide.png", f"{U}/ppt/media/mock-wide.png")

    # final order -> source file; new slides are slide12..14
    order = ["slide1", "slide2", "slide3", "slide4", "NEW_MOCKUP", "slide5", "slide6", "slide7", "slide8",
             "NEW_PLAN", "slide9", "slide10", "NEW_FUTURE", "slide11"]
    new = {
        "NEW_MOCKUP": (12, mockup_slide(5), "image-2-1.png", ["mock-driver.png", "mock-wide.png"]),
        "NEW_PLAN": (13, plan_slide(10), "image-8-1.png", []),
        "NEW_FUTURE": (14, future_slide(13), "image-7-1.png", []),
    }
    rid = {}
    for key, (num, sl, icon, imgs) in new.items():
        rid[key] = add_slide(num, sl, icon, imgs)

    # existing slides: renumber kickers + footers, text fixes
    kicker_map = {"04 · ESG — ENVIRONMENTAL": "05 · ESG — ENVIRONMENTAL",
                  "05 · ESG — SOCIAL &amp; GOVERNANCE": "06 · ESG — SOCIAL &amp; GOVERNANCE",
                  "06 · INNOVATION": "07 · INNOVATION", "07 · FEASIBILITY": "08 · FEASIBILITY",
                  "08 · USER EXPERIENCE": "10 · USER EXPERIENCE", "09 · MEASUREMENT &amp; KPIs": "11 · MEASUREMENT &amp; KPIs"}
    for page, src in enumerate(order, start=1):
        if src.startswith("NEW"):
            continue
        p = f"{SL}/{src}.xml"
        x = read(p)
        x = re.sub(r"<a:t>\d\d / 11</a:t>", f"<a:t>{page:02d} / {TOTAL}</a:t>", x)
        for a, b in kicker_map.items():
            x = x.replace(f"<a:t>{a}</a:t>", f"<a:t>{b}</a:t>")
        if src == "slide8":
            x = x.replace("<a:t>ความเป็นไปได้และแผนการนำไปใช้จริง</a:t>", "<a:t>ความเป็นไปได้ในการนำไปใช้จริง</a:t>")
        if src == "slide9":
            old = "เซนเซอร์วัดอากาศตัวเดียวกันบันทึกข้อมูลสภาพแวดล้อมการทำงานต่อเนื่อง ซึ่งไม่เคยมีการตรวจวัดมาก่อน"
            assert old in x, "UX air-sensor text not found"
            x = x.replace(old, "รถวนหาที่จอดน้อยลง ไอเสียในอาคารก็ลดลง ซึ่งเป็นผลดีกับคนที่ต้องทำงานในพื้นที่นี้ทั้งกะ")
        if src == "slide10":
            old = ("เก็บข้อมูลเพิ่มอีก 5 อย่าง: อัตราที่คนขับทำตามคำแนะนำ, จำนวนชั้นที่ต้องขับผ่านก่อนได้จอด, "
                   "ความยาวแถวรถตรงทางลาด, ปริมาณ CO/PM2.5 พร้อมชั่วโมงพัดลมระบายอากาศ, และความถี่ในการเปลี่ยนคำแนะนำ")
            assert old in x, "KPI text not found"
            x = x.replace(old, "เก็บข้อมูลเพิ่มอีก 4 อย่าง จากกล้องและเซนเซอร์ชุดเดิม ไม่ต้องติดอุปกรณ์เพิ่ม: "
                               "อัตราที่คนขับทำตามคำแนะนำ (เทียบอัตรารถเข้าชั้นตอนป้ายบอก “เข้าได้เลย” กับ “ขึ้นชั้นบน”), "
                               "จำนวนชั้นที่ต้องขับผ่านก่อนได้จอด, ความถี่ในการเปลี่ยนคำแนะนำ, "
                               "และ CO2e ที่ลดได้ (ข้อมูลเสริม: รอบที่เลี้ยวผิดที่ลดได้ × 0.4 km × 166 gCO2e/km)")
        write(p, x)

    # rebuild slide order
    pres = read(f"{U}/ppt/presentation.xml")
    old_ids = re.findall(r'<p:sldId id="(\d+)" r:id="(rId\d+)"/>', pres)
    by_src = {f"slide{n}": r for n, (_, r) in enumerate(old_ids, start=1)}
    by_src.update(rid)
    next_id = max(int(i) for i, _ in old_ids) + 1
    ids, used = [], {r: i for i, r in old_ids}
    for src in order:
        r = by_src[src]
        if r not in used:
            used[r] = str(next_id)
            next_id += 1
        ids.append(f'<p:sldId id="{used[r]}" r:id="{r}"/>')
    pres = re.sub(r"<p:sldIdLst>.*?</p:sldIdLst>", "<p:sldIdLst>" + "".join(ids) + "</p:sldIdLst>", pres, flags=re.S)
    write(f"{U}/ppt/presentation.xml", pres)

    out = "No_Cap_Pitch_Deck.pptx"
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        ct = f"{U}/[Content_Types].xml"
        z.write(ct, "[Content_Types].xml")
        for root, _, files in os.walk(U):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, U)
                if arc != "[Content_Types].xml":
                    z.write(full, arc)
    print("wrote", out)


if __name__ == "__main__":
    main()
