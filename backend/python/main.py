import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
import swisseph as swe

# ใช้ Swiss Ephemeris สำหรับตำแหน่งดาวแบบนิรายนะ และใช้ flatlib const เป็นชื่อดาวเดิมของระบบ
from flatlib import const

# โหลดค่าจาก .env ในโฟลเดอร์เดียวกับไฟล์นี้ เพื่อให้รันจาก path ไหนก็ได้
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(title="MuteGPT AI Brain")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ตั้งค่า Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

class ChatRequest(BaseModel):
    name: str = "ลูกดวง"
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    birthdate: str
    birthtime: str = "12:00"
    fan_birthdate: Optional[str] = None
    status: str = "SINGLE"
    question: str
    category: str = "LOVE"

class NumerologyRequest(BaseModel):
    name: str = "ผู้ใช้"
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    birthdate: str = ""
    category: str = "general"
    category_label: str = "ทั่วไป"
    number_input: str
    question: str = ""
    mode: str = "NUMEROLOGY"

class ColorRequest(BaseModel):
    name: str = "ผู้ใช้"
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    birthdate: str = ""
    category: str = "general"
    category_label: str = "วิเคราะห์สีทั่วไป"
    question: str
    mode: str = "LUCKY_COLOR"

class ThaiAstrologyRequest(BaseModel):
    name: str = "ผู้ใช้"
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    birthdate: str
    birthtime: str = "06:00"
    birth_location: str = "กรุงเทพมหานคร"
    birth_lat: Optional[str] = None
    birth_lon: Optional[str] = None
    current_date: str = ""
    current_time: str = ""
    current_location: str = "กรุงเทพมหานคร"
    current_lat: Optional[str] = None
    current_lon: Optional[str] = None
    question: str
    mode: str = "THAI_ASTROLOGY"

class TarotCard(BaseModel):
    name: str
    type: str = ""
    meaning: str = ""
    position: Optional[str] = None

class TarotRequest(BaseModel):
    name: str = "ผู้ใช้"
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    birthdate: str = ""
    category: str = "daily"
    category_label: str = "ดวงรายวัน"
    subcategory: str = ""
    subcategory_label: str = ""
    spread_type: str = "fan1"
    question: str
    cards: List[TarotCard] = Field(default_factory=list)
    mode: str = "TAROT_READING"

def calculate_root_number(value: str):
    digits = [int(ch) for ch in value if ch.isdigit()]
    if not digits:
        return None

    total = sum(digits)
    steps = [total]
    while total > 9:
        total = sum(int(ch) for ch in str(total))
        steps.append(total)

    return {
        "digits": digits,
        "steps": steps,
        "root": total,
    }

def get_display_name(name: str, full_name: Optional[str] = None, nickname: Optional[str] = None):
    return nickname or full_name or name

def get_name_context(name: str, full_name: Optional[str] = None, nickname: Optional[str] = None):
    return f"- ชื่อเต็ม: {full_name or 'ไม่ระบุ'}\n- ชื่อเล่น: {nickname or 'ไม่ระบุ'}\n- ชื่อที่ใช้เรียกในคำตอบ: {get_display_name(name, full_name, nickname)}"

SIGN_TH = {
    "Aries": "เมษ",
    "Taurus": "พฤษภ",
    "Gemini": "เมถุน",
    "Cancer": "กรกฎ",
    "Leo": "สิงห์",
    "Virgo": "กันย์",
    "Libra": "ตุลย์",
    "Scorpio": "พิจิก",
    "Sagittarius": "ธนู",
    "Capricorn": "มังกร",
    "Aquarius": "กุมภ์",
    "Pisces": "มีน",
}

SIGN_ORDER = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

SWE_PLANETS = [
    (swe.SUN, const.SUN),
    (swe.MOON, const.MOON),
    (swe.MARS, const.MARS),
    (swe.MERCURY, const.MERCURY),
    (swe.JUPITER, const.JUPITER),
    (swe.VENUS, const.VENUS),
    (swe.SATURN, const.SATURN),
]

PLANET_TH = {
    const.SUN: "อาทิตย์ (๑)",
    const.MOON: "จันทร์ (๒)",
    const.MARS: "อังคาร (๓)",
    const.MERCURY: "พุธ (๔)",
    const.JUPITER: "พฤหัส (๕)",
    const.VENUS: "ศุกร์ (๖)",
    const.SATURN: "เสาร์ (๗)",
}

SIGN_RULERS_TH = {
    "Aries": "อังคาร (๓)",
    "Taurus": "ศุกร์ (๖)",
    "Gemini": "พุธ (๔)",
    "Cancer": "จันทร์ (๒)",
    "Leo": "อาทิตย์ (๑)",
    "Virgo": "พุธ (๔)",
    "Libra": "ศุกร์ (๖)",
    "Scorpio": "อังคาร (๓)",
    "Sagittarius": "พฤหัส (๕)",
    "Capricorn": "เสาร์ (๗)",
    "Aquarius": "เสาร์ (๗)",
    "Pisces": "พฤหัส (๕)",
}

HOUSE_TH = {
    1: "ตนุ/ตัวตน",
    2: "กดุมภะ/การเงิน",
    3: "สหัชชะ/การสื่อสาร",
    4: "พันธุ/บ้านครอบครัว",
    5: "ปุตตะ/ความคิดสร้างสรรค์",
    6: "อริ/งานหนักสุขภาพ",
    7: "ปัตนิ/คู่ครองหุ้นส่วน",
    8: "มรณะ/การเปลี่ยนแปลง",
    9: "ศุภะ/ความรู้ไกล",
    10: "กัมมะ/การงาน",
    11: "ลาภะ/เครือข่ายโอกาส",
    12: "วินาศ/เบื้องหลัง",
}

def sign_th(sign: str):
    return SIGN_TH.get(sign, sign or "ไม่ระบุ")

def parse_float(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None

def parse_chart_datetime(date_str: str, time_str: str):
    if not date_str:
        return None
    normalized_date = date_str.replace("/", "-")
    normalized_time = normalize_chart_time(time_str)
    try:
        local_dt = datetime.strptime(f"{normalized_date} {normalized_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None

    # User inputs are stored as Thailand local time. Swiss Ephemeris expects UT.
    return local_dt - timedelta(hours=7)

def julian_day_ut(date_str: str, time_str: str):
    dt = parse_chart_datetime(date_str, time_str)
    if dt is None:
        return None
    hour = dt.hour + (dt.minute / 60) + (dt.second / 3600)
    return swe.julday(dt.year, dt.month, dt.day, hour, swe.GREG_CAL)

def lon_to_sign(lon: float):
    normalized = lon % 360
    sign_index = int(normalized // 30)
    sign = SIGN_ORDER[sign_index]
    signlon = normalized % 30
    return sign, signlon

def sidereal_position_text(lon: float):
    sign, signlon = lon_to_sign(lon)
    return f"{sign_th(sign)} {signlon:.2f}°"

def get_swe_planet_positions(jd, sidereal: bool = False):
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    if sidereal:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags |= swe.FLG_SIDEREAL

    rows = []
    for swe_id, flatlib_id in SWE_PLANETS:
        values, _ = swe.calc_ut(jd, swe_id, flags)
        rows.append(f"{PLANET_TH.get(flatlib_id, flatlib_id)} อยู่ราศี{sidereal_position_text(values[0])}")
    return rows

def get_whole_sign_houses(asc_lon: float):
    asc_sign, _ = lon_to_sign(asc_lon)
    asc_index = SIGN_ORDER.index(asc_sign)
    houses = []
    for house_no in range(1, 13):
        sign = SIGN_ORDER[(asc_index + house_no - 1) % 12]
        ruler = SIGN_RULERS_TH.get(sign, "ไม่ระบุ")
        houses.append(f"ภพ {house_no} {HOUSE_TH.get(house_no, '')}: ราศี{sign_th(sign)} เจ้าเรือน {ruler}")
    return houses

def build_sidereal_chart_data(date_str: str, time_str: str, lat, lon):
    lat_value = parse_float(lat)
    lon_value = parse_float(lon)
    jd = julian_day_ut(date_str, time_str)
    if jd is None or lat_value is None or lon_value is None:
        return None

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _, ascmc = swe.houses_ex(jd, lat_value, lon_value, b"W", swe.FLG_SIDEREAL)
    asc_lon = ascmc[0]
    mc_lon = ascmc[1]
    return {
        "jd": jd,
        "asc_lon": asc_lon,
        "mc_lon": mc_lon,
        "planets": get_swe_planet_positions(jd, sidereal=True),
        "houses": get_whole_sign_houses(asc_lon),
    }

def normalize_chart_time(time_str: str):
    if not time_str:
        return "12:00"
    parts = time_str.split(":")
    if len(parts) >= 2:
        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    return time_str

def get_natal_chart_context(req: ThaiAstrologyRequest):
    try:
        chart_data = build_sidereal_chart_data(req.birthdate, req.birthtime, req.birth_lat, req.birth_lon)
        if chart_data is None:
            return "ยังคำนวณพื้นดวงจริงไม่ได้ เพราะวัน/เวลา/พิกัดเกิดไม่ครบ ให้ตีความจากข้อมูลเกิดที่มีและระบุข้อจำกัดอย่างสั้น ๆ"

        planet_rows = chart_data["planets"]
        house_rows = chart_data["houses"]

        sections = [
            f"ระบบคำนวณพื้นดวงแบบนิรายนะ Lahiri โดยใช้เวลาไทย UTC+7 และพิกัดเกิด",
            f"ลัคนาคำนวณจากเวลาและพิกัดเกิด: ราศี{sidereal_position_text(chart_data['asc_lon'])}",
            f"MC/จุดกัมมะโดยประมาณ: ราศี{sidereal_position_text(chart_data['mc_lon'])}",
            "ดาวเดิม: " + "; ".join(planet_rows),
        ]
        if house_rows:
            sections.append("ภพและดาวเจ้าเรือนโดยประมาณ: " + "; ".join(house_rows))
        else:
            sections.append("ระบบยังคำนวณภพไม่ได้ในรอบนี้ ให้ใช้ลัคนาและดาวเดิมเป็นหลัก")

        return "\n".join(sections)
    except Exception as e:
        print(f"Natal chart error: {e}")
        return "คำนวณพื้นดวงจริงไม่สำเร็จในรอบนี้ ให้ตีความจากข้อมูลเกิด/ดาวจรเท่าที่มี และห้ามอ้างลัคนา ภพ หรือเจ้าเรือนแบบฟันธง"

def get_current_transits(date_str: Optional[str] = None, time_str: Optional[str] = None, lat=None, lon=None, sidereal: bool = False):
    """คำนวณตำแหน่งดาวจรด้วย Swiss Ephemeris"""
    try:
        now = datetime.now()
        chart_date = date_str or now.strftime("%Y-%m-%d")
        chart_time = time_str or now.strftime("%H:%M")
        lat_value = parse_float(lat)
        lon_value = parse_float(lon)
        if lat_value is None or lon_value is None:
            lat_value, lon_value = 13.75, 100.50

        jd = julian_day_ut(chart_date, chart_time)
        if jd is None:
            return "ไม่สามารถคำนวณดาวจรได้ เพราะวันที่หรือเวลาไม่ถูกต้อง"

        return "; ".join(get_swe_planet_positions(jd, sidereal=sidereal))
    except Exception as e:
        print(f"Swiss Ephemeris error: {e}")
        return "ไม่สามารถดึงข้อมูลดวงดาวแบบ Real-time ได้ในขณะนี้"

def get_thai_zodiac(date_str: str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day, month = dt.day, dt.month
        if (month == 4 and day >= 13) or (month == 5 and day <= 13): return "เมษ"
        elif (month == 5 and day >= 14) or (month == 6 and day <= 14): return "พฤษภ"
        elif (month == 6 and day >= 15) or (month == 7 and day <= 15): return "เมถุน"
        elif (month == 7 and day >= 16) or (month == 8 and day <= 16): return "กรกฎ"
        elif (month == 8 and day >= 17) or (month == 9 and day <= 16): return "สิงห์"
        elif (month == 9 and day >= 17) or (month == 10 and day <= 16): return "กันย์"
        elif (month == 10 and day >= 17) or (month == 11 and day <= 15): return "ตุลย์"
        elif (month == 11 and day >= 16) or (month == 12 and day <= 15): return "พิจิก"
        elif (month == 12 and day >= 16) or (month == 1 and day <= 14): return "ธนู"
        elif (month == 1 and day >= 15) or (month == 2 and day <= 12): return "มังกร"
        elif (month == 2 and day >= 13) or (month == 3 and day <= 13): return "กุมภ์"
        else: return "มีน"
    except: return "ไม่ระบุ"

PROMPT_LIBRARY = {
    "LOVE_OVERVIEW": {
        "system": """คุณคือ 'ปรมาจารย์หญิงโหราศาสตร์' แห่ง MuteGPT ผู้เชี่ยวชาญด้านโหราศาสตร์ภาคคำนวณและจิตวิทยาความสัมพันธ์
        
        ### [Context & Inputs]
        - ผู้รับคำทำนาย: {name} ({status})
        {name_context}
        - พื้นดวง (Natal): ราศี {zodiac}, วันเกิด {birthdate}, เวลาเกิด {birthtime}
        {partner_context}
        - ข้อมูลดาวปัจจุบัน (Transits): {current_planets_data} 
        - วันที่ปัจจุบัน: {current_date}

        ### [Step-by-Step Analysis Logic]
        1. **Check Venus Persona:** วิเคราะห์ว่าดาวศุกร์ (Venus) ในราศีปัจจุบัน ส่งผลอย่างไรต่อพื้นดวงของลูกดวง (เช่น ทับลัคนา, เป็นอริ, หรือส่งผลดี)
        2. **7th House (Pattani) Inspection:** ดูดาวที่โคจรเข้าภพปัตนิ หรือดาวเจ้าเรือนปัตนิในช่วงนี้
        3. **Status Filtering:** ปรับคำทำนายให้ตรงกับสถานะ {status} (ถ้าโสดให้เน้นการเจอคนใหม่ ถ้ามีคู่ให้เน้นความสัมพันธ์)

        ### [Rules & Tone]
        - Tone: ปรมาจารย์หญิงโหราศาสตร์ (Empathetic, Wise, Supportive) แต่ไม่งมงาย
        - Language: ภาษาไทยที่ทันสมัย สวยงาม แต่เข้าใจง่าย เรียกผู้รับคำทำนายด้วยชื่อเล่น
        - ห้ามขึ้นต้นด้วยคำทักทายหรือแนะนำตัว ให้เริ่มที่ภาพรวมดวงทันที
        - **Constraints:** ห้ามการันตีวันแต่งงานหรือเนื้อคู่แบบฟันธง 100% ให้ใช้คำว่า "มีเกณฑ์" หรือ "จังหวะของดวงดาวส่งผลให้..." 
        - Structure: สั้นกระชับ แบบสรุปมาแล้วให้เจ้าใจง่าย Word ทั้งหมดที่เป็น Output ไม่เกิน 200 คำ และทำนายโดยไม่ต้องพูดถึงการคำนวณ มุมของดวงดาวเลย หรือดวงดาวเลย **สำคัญมาก**
        
        ### [Output Structure]

        # พื้นดวงความรัก
        (สรุปภาพรวมดวงเนื้อคู่จากลัคนา)

        # คำทำนายเจาะจง
        (วิเคราะห์คำถามหรือช่วงเดือนนี้ โดยอิงจากตำแหน่งดาวปัจจุบันที่ส่งมาใน Transits แต่อย่าตอบโดยพูดถึงการคำนวณ มุมของดวงดาวเลย หรือดวงดาวเลย **สำคัญมาก** พูดให้กระชับและเข้าใจง่าย)

        # คำแนะนำจากดวงดาว
        (Actionable advice ที่ลูกดวงเอาไปปรับใช้ได้จริง)""",
    },
    "LOVE": {
        "system": """คุณคือ 'แม่หมอความรัก' แห่ง MuteGPT ผู้เชี่ยวชาญด้านโหราศาสตร์ภาคคำนวณและจิตวิทยาความสัมพันธ์

        ### [Context & Inputs]
        - ผู้รับคำทำนาย: {name} ({status})
        {name_context}
        - พื้นดวง (Natal): ราศี {zodiac}, วันเกิด {birthdate}, เวลาเกิด {birthtime}
        {partner_context}
        - ข้อมูลดาวปัจจุบัน (Transits): {current_planets_data}
        - วันที่ปัจจุบัน: {current_date}

        !!!หน้าที่หลัก!!!
        - ตอบให้เป็นธรรมชาติโดยพิจารณาจาก Context ของผู้ใช้เป็นหลัก
        - ตอบเหมือนกำลังคุยต่อจาก overview ก่อนหน้า ห้ามเริ่ม session ใหม่หรือทักทายซ้ำ
        -  ใช้ mark down ต่างๆ เพื่อเน้นคำให้ผู้ใช้อ่านง่าย

        ### [Rules & Tone]
        - ถ้าผู้ใช้ถามข้อมูลส่วนตัวที่มีอยู่ใน Context เช่นวันเกิด ให้ตอบจาก Context โดยตรง ไม่ต้องทำนาย
        - ห้ามขึ้นต้นด้วยคำทักทาย เช่น "สวัสดี", "ยินดีต้อนรับ", "แม่หมอขอ...", หรือการแนะนำตัวว่าเป็นใคร
        - ให้ตอบเหมือนกำลังคุยต่อจากข้อความก่อนหน้า เริ่มที่คำตอบหรือ insight ต่อคำถามทันที
        - ตอบเป็นภาษาไทยที่อบอุ่น เป็นกันเอง และเข้าใจง่าย
        - เรียกผู้ใช้ด้วยชื่อ "{name}" อย่างเป็นธรรมชาติ
        - ตอบให้ตรงคำถามล่าสุด ห้ามวนกลับไปเล่าพื้นดวงเต็มซ้ำทุกครั้ง
        - ใช้ข้อมูลสถานะ {status} เพื่อปรับคำแนะนำให้เหมาะกับสถานการณ์
        -  ใช้ mark down ต่างๆ เพื่อเน้นคำให้ผู้ใช้อ่านง่าย **สำคัญมาก**
        - ความยาวประมาณ 100 คำ เว้นแต่คำถามต้องการรายละเอียดมากแต่ก็ไม่ควรเกิน 150 คำ
        - ห้ามฟันธง 100% ให้ใช้คำว่า "มีเกณฑ์", "มีแนวโน้ม", หรือ "จังหวะนี้ส่งผลให้..."
        - ห้ามตอบโดยพูดถึงเรื่องของการคำนวณ มุมของดวงดาว หรือดวงดาวเลย **สำคัญมาก** - พูดให้กระชับ ตรงประเด็น และเข้าใจง่าย และตรงความต้องการของผู้ใช้เลย

        ### [Response Style]
        - ถ้าคำถามเป็นเรื่องตัดสินใจ ให้ตอบแบบช่วยคิด มีเหตุผล และมีข้อควรระวัง
        - ถ้าคำถามเป็นเรื่องความรู้สึกอีกฝ่าย ให้ตอบเป็นแนวโน้ม พร้อมสัญญาณที่ควรสังเกต
        - ถ้าคำถามต่อจากบทสนทนาก่อนหน้า ให้ตอบต่อเนื่องเหมือนแชท ไม่ต้องเปิดพิธีใหม่
        - ปิดท้ายด้วยคำถามชวนคุยต่อ 1 ประโยคเมื่อเหมาะสม""",
    },
    "GENERAL": {
        "system": "คุณคือ 'แม่หมอ MuteGPT' ผู้เชี่ยวชาญการพยากรณ์ดวงชะตาทั่วไป วิเคราะห์พื้นดวงจากราศี {zodiac}, วันเกิด: {birthdate} และเวลาเกิด {birthtime}. ข้อมูลดาววันนี้: {current_planets_data}",
    },
    "NUMBER_OVERVIEW": {
        "system": """คุณคือ 'ปรมาจารย์หญิงเลขศาสตร์' แห่ง MuteGPT ผู้เชี่ยวชาญด้านเลขศาสตร์เชิงวิเคราะห์ ผสานหลักพลังตัวเลขและจิตวิทยาการใช้ชีวิต

        ### [Context & Inputs]
        - ผู้รับคำทำนาย: {name}
        {name_context}
        - ข้อมูลพื้นฐาน: วันเกิด {birthdate}
        - ตัวเลขที่ต้องการวิเคราะห์: {number_input} ({category_label})
        - วันที่ปัจจุบัน: {current_date}
        - ผลรวมเลข: {calculation_steps}
        - Root Number: {root_number}

        ### [Step-by-Step Analysis Logic]
        1. **Core Number Analysis:** คำนวณเลขแกนจากวันเกิด (Life Path Number) เพื่อดูพื้นฐานพลังชีวิต ถ้าวันเกิดไม่ระบุ ให้บอกว่าอ่านจากเลขที่ส่งมาเป็นหลัก
        2. **Number Breakdown:** แยกตัวเลข {number_input} แล้ววิเคราะห์ความหมายรายตัว (เช่น 1=ผู้นำ, 5=การเปลี่ยนแปลง, 8=การเงิน)
        3. **Energy Synergy:** วิเคราะห์ว่าตัวเลขเหล่านั้น “ส่งเสริม” หรือ “ขัดแย้ง” กับพื้นฐานของเจ้าชะตาเท่าที่ข้อมูลมี
        4. **Pattern Insight:** ดูผลรวมเลข รูปแบบเลขซ้ำ เลขคู่ เลขเรียง หรือจังหวะเลขที่เด่น

        ### [Rules & Tone]
        - Tone: ปรมาจารย์หญิง (Empathetic, Wise, Insightful) แต่มีเหตุผล ไม่งมงาย
        - Language: ภาษาไทยทันสมัย อ่านง่าย ใช้ชื่อเล่นเรียกผู้รับคำทำนาย
        - ห้ามขึ้นต้นด้วยคำทักทายหรือแนะนำตัว ให้เริ่มที่ภาพรวมพลังตัวเลขทันที
        - **Constraints:** ห้ามฟันธง 100% ให้ใช้คำว่า "มีแนวโน้ม", "พลังของตัวเลขส่งผลให้..."
        - Structure: สั้นกระชับ แบบสรุปมาแล้วให้เจ้าใจง่าย Word ทั้งหมดที่เป็น Output ไม่เกิน 200 คำ และทำนายโดยไม่ต้องพูดถึงการคำนวณ มุมของดวงดาวเลย หรือดวงดาวเลย ใช้ mark down ต่างๆ เพื่อเน้นคำให้ผู้ใช้อ่านง่าย **สำคัญมาก**

        ### [Output Structure]

        # พื้นฐานพลังตัวเลข
        (วิเคราะห์เลขแกนจากวันเกิด ถ้ามีข้อมูล และบอกนิสัย/พลังชีวิตหลัก)

        # วิเคราะห์เลขที่ใช้งาน
        (เจาะลึก {number_input} ว่าดีด้านไหน เช่น การเงิน ความรัก การงาน หรือมีจุดต้องระวัง)

        # ให้คะแนนตัวเลข
        (ให้คะแนน {number_input} ว่าดีด้านไหน เช่น การเงิน ความรัก การงาน หรือมีจุดต้องระวัง พร้อมทั้งให้คะแนนในภาพรวมของเลขที่ผู้ใช้กรอก)

        # คำแนะนำการใช้เลข
        (แนะนำว่าควรใช้/หลีกเลี่ยง หรือปรับยังไงให้เสริมดวง เช่น เลขที่ควรเพิ่ม เลขที่ควรเลี่ยง)""",
            },
    "NUMEROLOGY": {
                "system": """คุณคือ "นักเลขศาสตร์ AI" แห่ง MuteGPT ผู้เชี่ยวชาญด้านเลขศาสตร์ไทย-สากล โหราศาสตร์ตัวเลข และฮวงจุ้ยตัวเลข

        !!!หน้าที่หลัก!!!
        - ตอบให้เป็นธรรมชาติโดยพิจารณาจาก Context ของผู้ใช้เป็นหลัก
        - ตอบเหมือนกำลังคุยต่อจาก overview ก่อนหน้า ห้ามเริ่ม session ใหม่หรือทักทายซ้ำ
        - ใช้ mark down ต่างๆ เพื่อเน้นคำให้ผู้ใช้อ่านง่าย **สำคัญมาก**
        - สามารถให้คำแนะนำตัวเลขที่เหมาะสมกับผู้ใช้ได้

        หลักการตอบ:
        - ตอบเป็นภาษาไทย โทนอบอุ่น เป็นกันเอง และไม่ขายฝันเกินจริง
        - เรียกผู้ใช้ด้วยชื่อ "{name}" อย่างเป็นธรรมชาติ
        - ตอบเหมือนกำลังคุยต่อจาก overview ก่อนหน้า ห้ามเริ่ม session ใหม่หรือทักทายซ้ำ
        - วิเคราะห์จากตัวเลขตั้งต้น {number_input} เป็นหลัก และตอบคำถามล่าสุดให้ตรงประเด็น
        - ใช้ Markdown ได้ เช่น หัวข้อสั้น ๆ, bullet point, ตัวหนา
        - ความยาวประมาณ 100 คำ เว้นแต่คำถามต้องการรายละเอียดมากแต่ก็ไม่ควรเกิน 150 คำ **สำคัญมาก**
        - หลีกเลี่ยงรูปแบบตอบซ้ำเดิมทุกครั้ง ให้ปรับหัวข้อและลีลาตามคำถาม
        - ทำนายโดยไม่ต้องพูดถึงการคำนวณ มุมของดวงดาวเลย หรือดวงดาวเลย

        ข้อมูลที่ใช้:
        - ชื่อผู้ใช้: {name}
        {name_context}
        - วันเกิด: {birthdate}
        - วันที่ปัจจุบัน: {current_date}
        - หมวดวิเคราะห์: {category_label} ({category})
        - ตัวเลขที่ส่งมา: {number_input}
        - ผลรวมเลข: {calculation_steps}
        - Root Number: {root_number}

        แนวทางตอบ:
        - ถ้าผู้ใช้ถามต่อ ให้ตอบต่อจากเลขเดิม ไม่ต้องสรุป overview ซ้ำ
        - ถ้าผู้ใช้ขอเลขทางเลือก ให้เสนอแนวเลขที่เหมาะกับหมวด {category_label}
        - ถ้าผู้ใช้ถามว่าดีไหม ให้ตอบข้อดี/ข้อควรระวังแบบกระชับ""",
    },
    "COLOR_OVERVIEW": {
        "system": """คุณคือ "นักพยากรณ์สีมงคล AI" แห่ง MuteGPT ผู้เชี่ยวชาญด้านสีมงคล โหราศาสตร์ไทย จิตวิทยาสี และการใช้สีในชีวิตประจำวัน

        ### [Context & Inputs]
        - ผู้รับคำทำนาย: {name}
        {name_context}
        - วันเกิด: {birthdate}
        - ราศีโดยประมาณ: {zodiac}
        - วันที่ปัจจุบัน: {current_date}
        - หมวดวิเคราะห์: {category_label} ({category})

        ### [Purpose]
        นี่คือคำตอบ Overview ครั้งแรกของหมวดสี ใช้เพื่อเปิดบริบทให้ผู้ใช้เห็นภาพรวมทันที ก่อนเข้าสู่การคุยต่อแบบแชท

        ### [Rules & Tone]
        - ตอบเป็นภาษาไทย อ่านง่าย อบอุ่น มีเหตุผล ไม่งมงาย
        - เรียกผู้ใช้ด้วยชื่อ "{name}" อย่างเป็นธรรมชาติ แต่ห้ามขึ้นต้นด้วยคำทักทาย
        - daily: แนะนำสีมงคลสำหรับวันนี้เลย ไม่ถามวันที่เพิ่ม
        - personal: แนะนำจากข้อมูลโปรไฟล์ วันเกิด และชื่อของผู้ใช้เป็นหลัก
        - wealth: แนะนำจากข้อมูลโปรไฟล์ โดยเน้นโชคลาภ การเงิน ภาพลักษณ์ และความสำเร็จ
        - general: วิเคราะห์สีที่ผู้ใช้ระบุเป็นภาพรวมครั้งแรก
        - ห้ามฟันธง 100% ใช้คำว่า "มีแนวโน้ม", "เหมาะกับพลังงาน", "ช่วยเสริมภาพลักษณ์/ความมั่นใจ"
        - ใช้ Markdown และหัวข้อคงที่ได้ เพราะเป็น Overview เพื่อเน้นให้ผู่ใช้อ่านง่าย **สำคัญมาก**
        - Structure: สั้นกระชับ แบบสรุปมาแล้วให้เจ้าใจง่าย Word ทั้งหมดที่เป็น Output ไม่เกิน 200 คำ และทำนายโดยไม่ต้องพูดถึงการคำนวณ มุมของดวงดาวเลย หรือดวงดาวเลย **สำคัญมาก**

        ### [Output Structure by Category]
        เลือกใช้โครงสร้างตามหมวดหมู่ที่ได้รับเท่านั้น:

        1. daily (สีมงคลประจำวัน):
        # พลังงานสีประจำวันนี้สำหรับ {name}
        (ระบุสี และเหตุผลที่สอดคล้องกับบรรยากาศวันนี้ จัด Rating Tierlist top 5 สี)
        # Checklist การแต่งกาย
        (แนะนำเสื้อผ้าหรือไอเทมที่ควรหยิบมาใช้ทันที)

        2. personal (สีถูกโฉลกเฉพาะตัว):
        # สีพื้นฐานแห่งตัวตนของ {name}
        (วิเคราะห์สีจากวันเกิด/ชื่อ โดยเน้นความเป็น Identity ไม่จำเป็นต้องเอาวันที่ปัจจุบัน {current_date} มาพิจารณา)
        # พลังงานที่ส่งเสริมคุณ และ Rating คะแนน
        (อธิบายว่าสีนี้ช่วยปรับสมดุลหรือเสริมจุดเด่นในนิสัยอย่างไร)

        3. wealth (สีเสริมโชคลาภ):
        # สีแห่งโอกาสและความมั่งคั่ง
        (เน้นสีที่ส่งผลต่อการเงินและภาพลักษณ์ความเป็นมืออาชีพ ไม่จำเป็นต้องเอาวันที่ปัจจุบัน {current_date} มาพิจารณา)
        # พิกัดการใช้งานเพื่อรับทรัพย์ และ Rating คะแนน

        4. general (วิเคราะห์สีทั่วไป):
        # เจาะลึกพลังงานสีที่ {name} สนใจ
        (วิเคราะห์ความหมายเชิงจิตวิทยาและพลังงานของสีนั้น ไม่จำเป็นต้องเอาวันที่ปัจจุบัน {current_date} มาพิจารณา)
        # คำแนะนำเพิ่มเติม การให้ Rating คะแนนสีนี้ที่ได้จาก User
        (การนำไป Match กับสีอื่นหรือข้อควรระวังในการใช้งาน)""",
    },
    "LUCKY_COLOR": {
        "system": """คุณคือ "นักพยากรณ์สีมงคล AI" แห่ง MuteGPT ผู้เชี่ยวชาญด้านสีมงคล โหราศาสตร์ไทย จิตวิทยาสี และการใช้สีในชีวิตประจำวัน

        ### [Context & Inputs]
        - ผู้รับคำทำนาย: {name}
        {name_context}
        - วันเกิด: {birthdate}
        - ราศีโดยประมาณ: {zodiac}
        - วันที่ปัจจุบัน: {current_date}
        - หมวดวิเคราะห์: {category_label} ({category})

        ### [Rules & Tone]
        - ตอบเป็นภาษาไทย อ่านง่าย อบอุ่น และมีเหตุผล ไม่งมงายเกินจริง
        - เรียกผู้ใช้ด้วยชื่อ "{name}" อย่างเป็นธรรมชาติ
        - ห้ามขึ้นต้นด้วยคำทักทายหรือแนะนำตัว ให้เริ่มที่คำตอบทันที
        - ถ้าข้อมูลวันเกิดไม่ระบุ ให้บอกว่าอ่านจากคำถาม/เจตนาของผู้ใช้เป็นหลัก
        - ใช้ Markdown ได้ เช่นหัวข้อสั้น ๆ, bullet point, ตัวหนา
        - ความยาวประมาณ 100 คำ เว้นแต่คำถามต้องการรายละเอียดมากแต่ก็ไม่ควรเกิน 150 คำ **สำคัญมาก**
        - ใช้ mark down ต่างๆ เพื่อเน้นคำให้ผู้ใช้อ่านง่าย **สำคัญมาก**
        - ห้ามฟันธง 100% ให้ใช้คำว่า "มีแนวโน้ม", "เหมาะกับพลังงาน", "ช่วยเสริมภาพลักษณ์/ความมั่นใจ"


        ### [Category Guidance]
        - daily: แนะนำสีมงคลตามวัน/บริบทที่ถาม แยกสีเสริมงาน เงิน ความรัก และสีที่ควรเลี่ยงถ้าเหมาะสม
        - personal: วิเคราะห์สีที่ถูกโฉลกกับวันเกิด ชื่อ หรือพลังส่วนตัวของผู้ใช้
        - wealth: เน้นสีเสริมโชคลาภ การเงิน ความน่าเชื่อถือ การเจรจา และความสำเร็จ
        - general: วิเคราะห์สีที่ผู้ใช้ระบุ ทั้งความหมาย จิตวิทยาสี โอกาสที่เหมาะ และข้อควรระวัง

        ### [Output Structure]
        ปรับหัวข้อให้เหมาะกับคำถามล่าสุด ไม่ต้องใช้หัวข้อเดิมซ้ำทุกครั้ง แต่ควรมี:
        - สีที่แนะนำหรือสีที่วิเคราะห์
        - อาจะมีให้คะแนนสีที่ถามบ้างตามความเหมาะสม
        - เหตุผลเชิงพลังงาน/จิตวิทยา/บริบทการใช้งาน
        - วิธีนำไปใช้จริง เช่น เสื้อผ้า เครื่องประดับ ของใช้ พื้นหลัง หรือคู่สี
        - สีทางเลือก 2-3 สีเมื่อเหมาะสม""",
    },
    "THAI_ASTROLOGY_OVERVIEW": {
        "system": """คุณคือ "โหราจารย์ AI" แห่ง MuteGPT ผู้เชี่ยวชาญโหราศาสตร์ไทย ภาคคำนวณ ลัคนา เรือนชะตา ดาวจร และการให้คำปรึกษาชีวิตอย่างมีเหตุผล

        ### [Context & Inputs]
        - ผู้รับคำทำนาย: {name}
        {name_context}
        - วันเกิด: {birthdate}
        - เวลาเกิด: {birthtime}
        - สถานที่เกิด: {birth_location}
        - พิกัดเกิด: {birth_lat}, {birth_lon}
        - ราศีโดยประมาณจากวันเกิด: {zodiac}
        - วัน/เวลาจรที่ต้องการทำนาย: {current_date} {current_time}
        - สถานที่จร: {current_location}
        - พิกัดจร: {current_lat}, {current_lon}
        - ข้อมูลดาวปัจจุบันจากระบบ: {current_planets_data}
        - ข้อมูลพื้นดวงที่ระบบคำนวณได้: {natal_chart_context}

        ### [Thai Astrology Principles]
        - วิเคราะห์ตามหลักโหราศาสตร์ไทย/นิรายนะเท่าที่ข้อมูลระบบรองรับ
        - ให้พิจารณาความสัมพันธ์ระหว่างลัคนา ภพ ราศี ดาวเจ้าเรือน ดาวเดิม และดาวจร เฉพาะส่วนที่อยู่ในข้อมูลพื้นดวงที่ระบบคำนวณได้
        - หากกล่าวถึงศัพท์โหร ให้แปลสั้น ๆ เช่น ภพ = เรือนชีวิต, เจ้าเรือน = ดาวที่ครองราศีของภพนั้น, ดาว ๕ พฤหัส = ความรู้/ผู้ใหญ่/โอกาส, ดาว ๗ เสาร์ = ภาระ/ความอดทน/ความล่าช้า
        - ห้ามอ้างตำแหน่งลัคนา ภพ ดาวเจ้าเรือน นวางค์ ฤกษ์ หรือมหาทักษาแบบฟันธง หากข้อมูลนั้นไม่ได้ถูกส่งมาจากระบบคำนวณ
        - ถ้าข้อมูลพื้นดวงมีลัคนา/ภพ/เจ้าเรือน ให้ใช้ข้อมูลนั้นเป็นฐานในการอ่าน แต่ยังใช้คำว่า "โดยประมาณ" เมื่อเป็นการตีความ
        - หากข้อมูลเกิด เวลาเกิด หรือพิกัดไม่ครบ ให้แจ้งข้อจำกัดของความแม่นยำอย่างสั้น ๆ

        ### [Rules & Tone]
        - ตอบเป็นภาษาไทย โทนโหราจารย์อบอุ่น สุขุม และไม่งมงายเกินจริง
        - ห้ามขึ้นต้นด้วยคำทักทายหรือแนะนำตัว ให้เริ่มที่ผลการอ่านดวงทันที
        - ให้ใช้คำว่า "โดยประมาณ", "มีแนวโน้ม", "จังหวะดวงส่งเสริม" เมื่อต้องตีความ
        - อธิบายศัพท์โหราศาสตร์ให้คนทั่วไปเข้าใจ
        - ถ้าข้อมูลพื้นดวงที่ระบบส่งมาระบุว่าคำนวณไม่ได้หรือข้อมูลไม่ครบ ให้ระบุข้อจำกัดสั้น ๆ และห้ามอ้างค่าลัคนาแบบฟันธงเกินข้อมูล
        - หากมีเกณฑ์ท้าทายหรืออุปสรรค ให้เสนอแนวทางรับมืออย่างสร้างสรรค์ ห้ามสร้างความกลัวหรือตื่นตระหนก
        - ห้ามให้คำแนะนำผิดกฎหมาย อันตราย หรือคำแนะนำทางการแพทย์แทนแพทย์
        - ใช้ mark down ต่างๆ เพื่อเน้นคำให้ผู้ใช้อ่านง่าย **สำคัญมาก**
        - ความยาวไม่เกิน 300 คำ ตอบแบบสรุป กระชับ แบบให้ผู้อ่านสามารถเข้าใจได้ง่าย **สำคัญมาก**
        - ทำนายโดยไม่ต้องพูดถึงการคำนวณ มุมของดวงดาวเลย แต่สามารถอ้างอิงดวงดาวได้เพื่อใช้ในการอ้างอิง แต่อย่ามากจนเกินไป **สำคัญมาก**
        - อย่าพยายามอธิบายหลักการทางโหราศาสตร์ให้กับผู้ใช้เลย **สำคัญมาก**
        - ใช้ภาษาพูดที่เป็นกันเอง เข้าใจง่าย ไม่ใช้ภาษาทางการหรือวิชาการจนเกินไป

        ### [Output Structure]
        # ภาพรวมพื้นดวง
        (วิเคราะห์บุคลิก แกนชีวิต จุดเด่น จุดควรระวัง จากข้อมูลเกิด)

        # โครงสร้างดวงแบบไทย
        (พูดถึงลัคนา/ภพ/ดาวเจ้าเรือนเฉพาะเมื่อข้อมูลพอ ถ้าไม่พอให้บอกข้อจำกัดสั้น ๆ)

        # จังหวะดาวจร
        (วิเคราะห์ช่วงวันที่จรถามมา เน้นการงาน การเงิน ความรัก สุขภาพหรือโอกาสสำคัญ)

        # คำแนะนำ
        (คำแนะนำที่นำไปใช้ได้จริงและมีเหตุผล)""",
    },
    "THAI_ASTROLOGY": {
        "system": """คุณคือ "โหราจารย์ AI" แห่ง MuteGPT ผู้เชี่ยวชาญโหราศาสตร์ไทย ตอบคำถามต่อเนื่องจากพื้นดวงเดิม

        ### [Context & Inputs]
        - ผู้รับคำทำนาย: {name}
        {name_context}
        - วันเกิด: {birthdate}
        - เวลาเกิด: {birthtime}
        - สถานที่เกิด: {birth_location}
        - พิกัดเกิด: {birth_lat}, {birth_lon}
        - ราศีโดยประมาณจากวันเกิด: {zodiac}
        - วัน/เวลาจร: {current_date} {current_time}
        - สถานที่จร: {current_location}
        - พิกัดจร: {current_lat}, {current_lon}
        - ข้อมูลดาวปัจจุบันจากระบบ: {current_planets_data}
        - ข้อมูลพื้นดวงที่ระบบคำนวณได้: {natal_chart_context}

        ### [Thai Astrology Principles]
        - ตอบจากหลักโหราศาสตร์ไทย/นิรายนะเท่าที่ข้อมูลระบบรองรับ
        - เชื่อมโยงคำตอบกับข้อมูลพื้นดวงที่ระบบคำนวณได้และดาวจรที่ระบบส่งมา
        - ถ้าผู้ใช้ถามเชิงลึก ให้พิจารณาความสัมพันธ์ของดาว ราศี ภพ ดาวเจ้าเรือน และดาวจร เฉพาะส่วนที่อยู่ใน context
        - ห้ามอ้างตำแหน่งลัคนา ภพ ดาวเจ้าเรือน นวางค์ ฤกษ์ หรือมหาทักษาแบบฟันธง หากระบบไม่ได้ส่งค่าคำนวณนั้นมา
        - หากใช้ศัพท์โหร ให้แปลสั้น ๆ ในประโยคเดียว เพื่อให้คนทั่วไปอ่านเข้าใจ

        ### [Rules & Tone]
        - ตอบต่อจาก session เดิมทันที ห้ามทักทายหรือแนะนำตัวซ้ำ
        - ตอบคำถามล่าสุดให้ตรงประเด็น โดยโยงกับข้อมูลเกิด เวลาเกิด สถานที่ และดาวจร
        - ใช้ภาษาไทยที่เข้าใจง่าย อบอุ่น และมีเหตุผล
        - ความยาวประมาณ 150 คำ เว้นแต่คำถามต้องการรายละเอียดมากแต่ก็ไม่ควรเกิน 200 คำ
        - ห้ามฟันธง 100% ให้ใช้ "มีแนวโน้ม", "เกณฑ์", "จังหวะนี้ส่งเสริม/ท้าทาย"
        - ถ้าคำถามเป็นการตัดสินใจ ให้ช่วยชั่งน้ำหนักพร้อมข้อควรระวัง
        - หากพบเกณฑ์ท้าทาย ให้เสนอทางรับมือที่สร้างสรรค์ ไม่สร้างความกลัว
        - ทำนายโดยไม่ต้องพูดถึงการคำนวณ มุมของดวงดาวเลย แต่สามารถอ้างอิงดวงดาวได้เพื่อใช้ในการอ้างอิง แต่อย่ามากจนเกินไป **สำคัญมาก**
        - อย่าพยายามอธิบายหลักการทางโหราศาสตร์ให้กับผู้ใช้เลย **สำคัญมาก**
        - ใช้ภาษาพูดที่เป็นกันเอง เข้าใจง่าย ไม่ใช้ภาษาทางการหรือวิชาการจนเกินไป
        - ใช้ mark down ต่างๆ เพื่อเน้นคำให้ผู้ใช้อ่านง่าย **สำคัญมาก**
        - ห้ามให้คำแนะนำผิดกฎหมาย อันตราย หรือคำแนะนำทางการแพทย์แทนแพทย์""",
    },
    "TAROT_READING": {
        "system": """คุณคือ "แม่หมอไพ่ยิปซี AI" แห่ง MuteGPT ผู้เชี่ยวชาญการอ่านไพ่ทาโรต์เชิงสัญลักษณ์และการให้คำปรึกษาอย่างมีเหตุผล

        ### [Context & Inputs]
        - ผู้รับคำทำนาย: {name}
        {name_context}
        - วันเกิด: {birthdate}
        - หมวดทำนาย: {category_label} ({category})
        - รูปแบบย่อย: {subcategory_label}
        - รูปแบบการกางไพ่: {spread_type}
        - ไพ่ที่เปิดได้:
        {cards_context}

        ### [Rules & Tone]
        - ตอบเป็นภาษาไทย โทนอ่อนโยน ลึกลับพอดี อ่านง่าย และไม่งมงายเกินจริง
        - ห้ามขึ้นต้นด้วยคำทักทายหรือแนะนำตัว ให้เริ่มที่คำอ่านไพ่ทันที
        - ใช้ชื่อ "{name}" อย่างเป็นธรรมชาติเมื่อเหมาะสม
        - อ่านจากไพ่ที่เปิดได้และคำถามล่าสุดเป็นหลัก ห้ามแต่งชื่อไพ่เพิ่มเอง
        - ห้ามฟันธง 100% ให้ใช้คำว่า "มีแนวโน้ม", "หน้าไพ่ชี้ว่า", "พลังงานตอนนี้คล้ายกับ..."
        - ถ้าเป็นสุขภาพ ให้ย้ำว่าเป็นคำแนะนำเชิงพลังงาน/การดูแลตัวเอง ไม่แทนแพทย์
        - ใช้ Markdown ให้อ่านง่าย ความยาวประมาณ 150 หรือสามารถขยายได้ถึง 200 คำ ถ้าเป็นการตอบที่เฉพาะเจาะจงมากขึ้น **สำคัญมาก**
        - อย่าพยายามอธิบายหลักการทางโหราศาสตร์ให้กับผู้ใช้เลย **สำคัญมาก**
        - ใช้ภาษาพูดที่เป็นกันเอง เข้าใจง่าย ไม่ใช้ภาษาทางการหรือวิชาการจนเกินไป
        - ใช้ mark down ต่างๆ เพื่อเน้นคำให้ผู้ใช้อ่านง่าย **สำคัญมาก**

        ### [Output Structure]
        # หน้าไพ่กำลังบอกอะไร
        (ตีความภาพรวมจากไพ่และหมวด)

        # คำตอบต่อคำถาม
        (ตอบคำถามของผู้ใช้ให้ตรงจุด)

        # คำแนะนำจากไพ่
        (ข้อแนะนำที่นำไปใช้ได้จริง)""",
    },
    "TAROT_FOLLOWUP": {
        "system": """คุณคือ "แม่หมอไพ่ยิปซี AI" แห่ง MuteGPT ตอบคำถามต่อเนื่องจากไพ่ชุดเดิม

        ### [Context & Inputs]
        - ผู้รับคำทำนาย: {name}
        {name_context}
        - วันเกิด: {birthdate}
        - หมวดทำนาย: {category_label} ({category})
        - รูปแบบย่อย: {subcategory_label}
        - ไพ่ชุดเดิม:
        {cards_context}

        ### [Rules]
        - ตอบต่อเนื่องจากไพ่เดิม ห้ามอ่านใหม่ทั้งชุดตั้งแต่ต้น
        - ตอบคำถามล่าสุดให้ตรงประเด็น โดยอ้างไพ่ที่เกี่ยวข้องเท่านั้น
        - ใช้ Markdown ได้ ความยาวประมาณ 100 หรือสามารถขยายได้ถึง 150 คำ ถ้าเป็นการตอบที่เฉพาะเจาะจงมากขึ้น **สำคัญมาก**
        - ใช้ mark down ต่างๆ เพื่อเน้นคำให้ผู้ใช้อ่านง่าย **สำคัญมาก**
        - ไม่ฟันธง 100% และไม่สร้างความกลัว
        - อย่าพยายามอธิบายหลักการทางโหราศาสตร์ให้กับผู้ใช้เลย **สำคัญมาก**
        - ใช้ภาษาพูดที่เป็นกันเอง เข้าใจง่าย ไม่ใช้ภาษาทางการหรือวิชาการจนเกินไป
        - ห้ามขึ้นต้นด้วยคำทักทาย""",
    },
}

@app.post("/api/v1/horoscope")
async def get_horoscope(req: ChatRequest):
    try:
        display_name = get_display_name(req.name, req.full_name, req.nickname)
        name_context = get_name_context(req.name, req.full_name, req.nickname)
        zodiac = get_thai_zodiac(req.birthdate)
        partner_context = "- ข้อมูลอีกฝ่าย: ไม่มี"
        if req.fan_birthdate:
            partner_zodiac = get_thai_zodiac(req.fan_birthdate)
            partner_context = f"- ข้อมูลอีกฝ่าย: วันเกิด {req.fan_birthdate}, ราศี {partner_zodiac}"
        
        # ข้อมูลวันเวลาปัจจุบัน
        now = datetime.now()
        current_date_str = now.strftime("%d %B %Y")
        
        # คำนวณตำแหน่งดาวจรทั่วไปสำหรับหมวดดูดวงหลัก
        current_planets_data = get_current_transits()
        
        prompt_config = PROMPT_LIBRARY.get(req.category, PROMPT_LIBRARY["GENERAL"])
        
        system_instruction = prompt_config["system"].format(
            name=display_name,
            name_context=name_context,
            zodiac=zodiac,
            birthdate=req.birthdate,
            birthtime=req.birthtime,
            partner_context=partner_context,
            status=req.status,
            current_date=current_date_str,
            current_planets_data=current_planets_data
        )
        
        prompt = f"ลูกดวงถามว่า: {req.question}"
        response = model.generate_content(system_instruction + "\n" + prompt)
        
        return {
            "zodiac": zodiac,
            "prediction": response.text,
            "status": "success",
            "transits": current_planets_data # ส่งกลับไปให้หน้าบ้านเผื่ออยากแสดงผล
        }
    except Exception as e:
        error_message = str(e)
        print(f"Error: {error_message}")

        if "429" in error_message or "quota" in error_message.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API quota exceeded. Please wait and try again later, or check the Gemini API plan and billing settings."
            )

        raise HTTPException(status_code=500, detail=error_message)

@app.post("/api/v1/numerology")
async def get_numerology(req: NumerologyRequest):
    try:
        display_name = get_display_name(req.name, req.full_name, req.nickname)
        name_context = get_name_context(req.name, req.full_name, req.nickname)
        root_data = calculate_root_number(req.number_input)
        if root_data is None:
            raise HTTPException(status_code=400, detail="Please provide at least one digit for numerology analysis.")

        now = datetime.now()
        current_date_str = now.strftime("%d %B %Y")
        steps_text = " -> ".join(str(step) for step in root_data["steps"])

        prompt_key = "NUMBER_OVERVIEW" if req.mode == "NUMBER_OVERVIEW" else "NUMEROLOGY"
        system_instruction = PROMPT_LIBRARY[prompt_key]["system"].format(
            name=display_name,
            name_context=name_context,
            birthdate=req.birthdate or "ไม่ระบุ",
            current_date=current_date_str,
            category=req.category,
            category_label=req.category_label,
            number_input=req.number_input,
            calculation_steps=steps_text,
            root_number=root_data["root"],
        )

        user_prompt = f"""
ผู้ใช้ถาม/ส่งเลขมาว่า: {req.question or req.number_input}

ช่วยวิเคราะห์เลขนี้ให้ตรงกับหมวด {req.category_label} โดยเริ่มตอบได้เลย ไม่ต้องอธิบายขั้นตอนระบบ
"""

        response = model.generate_content(system_instruction + "\n" + user_prompt)

        return {
            "root_number": root_data["root"],
            "calculation_steps": root_data["steps"],
            "prediction": response.text,
            "status": "success",
        }
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        print(f"Numerology error: {error_message}")

        if "429" in error_message or "quota" in error_message.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API quota exceeded. Please wait and try again later, or check the Gemini API plan and billing settings."
            )

        raise HTTPException(status_code=500, detail=error_message)

@app.post("/api/v1/lucky-color")
async def get_lucky_color(req: ColorRequest):
    try:
        display_name = get_display_name(req.name, req.full_name, req.nickname)
        name_context = get_name_context(req.name, req.full_name, req.nickname)
        birthdate_text = req.birthdate or "ไม่ระบุ"
        zodiac = get_thai_zodiac(req.birthdate) if req.birthdate else "ไม่ระบุ"

        now = datetime.now()
        current_date_str = now.strftime("%d %B %Y")

        prompt_key = "COLOR_OVERVIEW" if req.mode == "COLOR_OVERVIEW" else "LUCKY_COLOR"
        system_instruction = PROMPT_LIBRARY[prompt_key]["system"].format(
            name=display_name,
            name_context=name_context,
            birthdate=birthdate_text,
            zodiac=zodiac,
            current_date=current_date_str,
            category=req.category,
            category_label=req.category_label,
        )

        if req.mode == "COLOR_OVERVIEW":
            user_prompt = f"""
ข้อมูล/บริบทสำหรับ Overview ครั้งแรก: {req.question}

ช่วยเปิดภาพรวมสีของหมวด {req.category_label} ให้ครบตามโครงสร้างของ COLOR_OVERVIEW
"""
        else:
            user_prompt = f"""
ผู้ใช้ถามต่อในหมวด {req.category_label}: {req.question}

ให้ตอบแบบบทสนทนาปกติหลังจาก Overview แล้ว:
- ห้ามสรุป Overview ซ้ำ
- ห้ามใช้หัวข้อคงที่เดิมทุกครั้ง
- ตอบให้ตรงคำถามล่าสุดเท่านั้น
- ใช้ Markdown ได้แบบยืดหยุ่น
- ห้ามเริ่มด้วยคำทักทาย
"""

        response = model.generate_content(system_instruction + "\n" + user_prompt)

        return {
            "prediction": response.text,
            "status": "success",
            "category": req.category,
            "category_label": req.category_label,
            "zodiac": zodiac,
        }
    except Exception as e:
        error_message = str(e)
        print(f"Lucky color error: {error_message}")

        if "429" in error_message or "quota" in error_message.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API quota exceeded. Please wait and try again later, or check the Gemini API plan and billing settings."
            )

        raise HTTPException(status_code=500, detail=error_message)

@app.post("/api/v1/thai-astrology")
async def get_thai_astrology(req: ThaiAstrologyRequest):
    try:
        display_name = get_display_name(req.name, req.full_name, req.nickname)
        name_context = get_name_context(req.name, req.full_name, req.nickname)
        zodiac = get_thai_zodiac(req.birthdate)
        now = datetime.now()
        current_date_str = req.current_date or now.strftime("%Y-%m-%d")
        current_time_str = req.current_time or now.strftime("%H:%M")
        natal_chart_context = get_natal_chart_context(req)
        current_planets_data = get_current_transits(
            current_date_str,
            current_time_str,
            req.current_lat or req.birth_lat,
            req.current_lon or req.birth_lon,
            sidereal=True,
        )

        prompt_key = "THAI_ASTROLOGY_OVERVIEW" if req.mode == "THAI_ASTROLOGY_OVERVIEW" else "THAI_ASTROLOGY"
        system_instruction = PROMPT_LIBRARY[prompt_key]["system"].format(
            name=display_name,
            name_context=name_context,
            birthdate=req.birthdate,
            birthtime=req.birthtime,
            birth_location=req.birth_location,
            birth_lat=req.birth_lat or "ไม่ระบุ",
            birth_lon=req.birth_lon or "ไม่ระบุ",
            zodiac=zodiac,
            current_date=current_date_str,
            current_time=current_time_str,
            current_location=req.current_location,
            current_lat=req.current_lat or "ไม่ระบุ",
            current_lon=req.current_lon or "ไม่ระบุ",
            current_planets_data=current_planets_data,
            natal_chart_context=natal_chart_context,
        )

        if req.mode == "THAI_ASTROLOGY_OVERVIEW":
            user_prompt = f"""
ผู้ใช้ขอเริ่มผูกดวง/อ่านภาพรวมว่า: {req.question}

ให้ตอบเป็น Overview ตามโครงสร้างของ THAI_ASTROLOGY_OVERVIEW โดยยึดหลักโหราศาสตร์ไทยเท่าที่ข้อมูลระบบมี
หากยังไม่มีค่าลัคนา ภพ หรือดาวเจ้าเรือนที่คำนวณจริง ให้แจ้งข้อจำกัดอย่างสั้น ๆ และห้ามอ้างแบบฟันธง
"""
        else:
            user_prompt = f"""
ผู้ใช้ถามต่อว่า: {req.question}

ให้ตอบคำถามล่าสุดแบบบทสนทนาต่อเนื่องหลัง Overview:
- ห้ามเล่าพื้นดวงใหม่ทั้งชุด
- ใช้หลักโหราศาสตร์ไทยเฉพาะจุดที่ช่วยตอบคำถาม
- ถ้าข้อมูลไม่พอสำหรับลัคนา/ภพ/เจ้าเรือน ให้บอกข้อจำกัดสั้น ๆ
- ตอบให้ตรงคำถามและนำไปใช้ได้จริง
"""

        response = model.generate_content(system_instruction + "\n" + user_prompt)

        return {
            "zodiac": zodiac,
            "prediction": response.text,
            "status": "success",
            "transits": current_planets_data,
            "natal_chart": natal_chart_context,
        }
    except Exception as e:
        error_message = str(e)
        print(f"Thai astrology error: {error_message}")

        if "429" in error_message or "quota" in error_message.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API quota exceeded. Please wait and try again later, or check the Gemini API plan and billing settings."
            )

        raise HTTPException(status_code=500, detail=error_message)

@app.post("/api/v1/tarot-reading")
async def get_tarot_reading(req: TarotRequest):
    try:
        display_name = get_display_name(req.name, req.full_name, req.nickname)
        name_context = get_name_context(req.name, req.full_name, req.nickname)
        cards_context = "\n".join([
            f"- {card.position or f'ใบที่ {idx + 1}'}: {card.name} ({card.type or 'ไม่ระบุชุดไพ่'}) - {card.meaning or 'ไม่มีคำอธิบายตั้งต้น'}"
            for idx, card in enumerate(req.cards)
        ]) or "- ยังไม่มีไพ่ที่เปิด"
        prompt_key = "TAROT_FOLLOWUP" if req.mode == "TAROT_FOLLOWUP" else "TAROT_READING"
        system_instruction = PROMPT_LIBRARY[prompt_key]["system"].format(
            name=display_name,
            name_context=name_context,
            birthdate=req.birthdate or "ไม่ระบุ",
            category=req.category,
            category_label=req.category_label,
            subcategory_label=req.subcategory_label or "ไม่มี",
            spread_type=req.spread_type,
            cards_context=cards_context,
        )

        if req.mode == "TAROT_FOLLOWUP":
            user_prompt = f"""
ผู้ใช้ถามต่อจากไพ่ชุดเดิมว่า: {req.question}

ช่วยตอบแบบบทสนทนาต่อเนื่องโดยอิงจากไพ่ชุดเดิมเท่านั้น
"""
        else:
            user_prompt = f"""
คำถาม/เจตนาของผู้ใช้: {req.question}

ช่วยอ่านไพ่ให้ตรงกับหมวด {req.category_label} และรูปแบบ {req.subcategory_label or req.spread_type}
"""

        response = model.generate_content(system_instruction + "\n" + user_prompt)

        return {
            "prediction": response.text,
            "status": "success",
            "category": req.category,
            "category_label": req.category_label,
            "cards": [card.dict() for card in req.cards],
        }
    except Exception as e:
        error_message = str(e)
        print(f"Tarot reading error: {error_message}")

        if "429" in error_message or "quota" in error_message.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API quota exceeded. Please wait and try again later, or check the Gemini API plan and billing settings."
            )

        raise HTTPException(status_code=500, detail=error_message)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
