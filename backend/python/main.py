import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Flatlib สำหรับคำนวณดาราศาสตร์
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
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

def get_current_transits():
    """คำนวณตำแหน่งดาวปัจจุบันโดยใช้ flatlib"""
    try:
        now = datetime.now()
        date_str = now.strftime('%Y/%m/%d')
        time_str = now.strftime('%H:%M')
        
        # ตั้งค่าเวลาและพิกัด (กรุงเทพฯ)
        date = Datetime(date_str, time_str, '+07:00')
        pos = GeoPos(13.75, 100.50)
        chart = Chart(date, pos)
        
        planets = [
            const.SUN, const.MOON, const.MARS, const.MERCURY, 
            const.JUPITER, const.VENUS, const.SATURN
        ]
        
        transit_data = []
        for p_id in planets:
            obj = chart.get(p_id)
            transit_data.append(f"{obj.id}: {obj.sign} ({obj.lon:.2f} deg)")
            
        return ", ".join(transit_data)
    except Exception as e:
        print(f"Flatlib error: {e}")
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
        - ความยาวประมาณ 180-360 คำ
        - ห้ามฟันธง 100% ให้ใช้คำว่า "มีแนวโน้ม", "เหมาะกับพลังงาน", "ช่วยเสริมภาพลักษณ์/ความมั่นใจ"

        ### [Category Guidance]
        - daily: แนะนำสีมงคลตามวัน/บริบทที่ถาม แยกสีเสริมงาน เงิน ความรัก และสีที่ควรเลี่ยงถ้าเหมาะสม
        - personal: วิเคราะห์สีที่ถูกโฉลกกับวันเกิด ชื่อ หรือพลังส่วนตัวของผู้ใช้
        - wealth: เน้นสีเสริมโชคลาภ การเงิน ความน่าเชื่อถือ การเจรจา และความสำเร็จ
        - general: วิเคราะห์สีที่ผู้ใช้ระบุ ทั้งความหมาย จิตวิทยาสี โอกาสที่เหมาะ และข้อควรระวัง

        ### [Output Structure]
        ปรับหัวข้อให้เหมาะกับคำถามล่าสุด ไม่ต้องใช้หัวข้อเดิมซ้ำทุกครั้ง แต่ควรมี:
        - สีที่แนะนำหรือสีที่วิเคราะห์
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

        ### [Rules & Tone]
        - ตอบเป็นภาษาไทย โทนโหราจารย์อบอุ่น สุขุม และไม่งมงายเกินจริง
        - ห้ามขึ้นต้นด้วยคำทักทายหรือแนะนำตัว ให้เริ่มที่ผลการอ่านดวงทันที
        - ให้ใช้คำว่า "โดยประมาณ", "มีแนวโน้ม", "จังหวะดวงส่งเสริม" เมื่อต้องตีความ
        - อธิบายศัพท์โหราศาสตร์ให้คนทั่วไปเข้าใจ
        - ถ้าระบบยังไม่ได้คำนวณลัคนาจริงแบบละเอียด ให้ระบุว่าอ่านจากข้อมูลเกิด/เวลา/สถานที่และดาวจรเป็นหลัก ห้ามอ้างค่าลัคนาแบบฟันธงเกินข้อมูล
        - ความยาวไม่เกิน 500 คำ

        ### [Output Structure]
        # ภาพรวมพื้นดวง
        (วิเคราะห์บุคลิก แกนชีวิต จุดเด่น จุดควรระวัง จากข้อมูลเกิด)

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

        ### [Rules & Tone]
        - ตอบต่อจาก session เดิมทันที ห้ามทักทายหรือแนะนำตัวซ้ำ
        - ตอบคำถามล่าสุดให้ตรงประเด็น โดยโยงกับข้อมูลเกิด เวลาเกิด สถานที่ และดาวจร
        - ใช้ภาษาไทยที่เข้าใจง่าย อบอุ่น และมีเหตุผล
        - ใช้ Markdown ได้ แต่ไม่ต้องใช้หัวข้อเดิมทุกครั้ง
        - ความยาวประมาณ 180-380 คำ
        - ห้ามฟันธง 100% ให้ใช้ "มีแนวโน้ม", "เกณฑ์", "จังหวะนี้ส่งเสริม/ท้าทาย"
        - ถ้าคำถามเป็นการตัดสินใจ ให้ช่วยชั่งน้ำหนักพร้อมข้อควรระวัง""",
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
        
        # คำนวณตำแหน่งดาวจริงด้วย Flatlib
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

        system_instruction = PROMPT_LIBRARY["LUCKY_COLOR"]["system"].format(
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
นี่คือคำขอ Overview ครั้งแรกของหมวด {req.category_label}

ข้อมูล/บริบทที่ต้องใช้วิเคราะห์: {req.question}

ให้ตอบเป็นภาพรวมสีมงคลครั้งแรกแบบนำไปใช้ได้ทันที:
- daily: แนะนำสีมงคลสำหรับวันนี้โดยไม่ต้องถามวันที่เพิ่ม
- personal: แนะนำจากข้อมูลโปรไฟล์ผู้ใช้เป็นหลัก
- wealth: แนะนำจากข้อมูลโปรไฟล์ผู้ใช้โดยเน้นโชคลาภ การเงิน และความสำเร็จ
- general: วิเคราะห์สีที่ผู้ใช้ระบุเป็น Overview ครั้งแรก

ห้ามเริ่มด้วยคำทักทายหรือแนะนำตัว ห้ามถามข้อมูลเพิ่มถ้าไม่จำเป็น
ใช้ Markdown กระชับ มีหัวข้อสั้นๆ และปิดท้ายด้วยคำชวนให้ถามต่อได้
"""
        else:
            user_prompt = f"""
ผู้ใช้ถามต่อในหมวด {req.category_label}: {req.question}

ให้ตอบต่อจากบริบทสี/หมวดเดิมแบบบทสนทนาปกติ ไม่ต้องสรุป Overview ซ้ำ
ตอบให้ตรงคำถามล่าสุด ใช้ Markdown ได้ และห้ามเริ่มด้วยคำทักทาย
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
        current_planets_data = get_current_transits()

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
        )

        user_prompt = f"""
ผู้ใช้ถาม/ขอวิเคราะห์ว่า: {req.question}

ช่วยอ่านดวงตามหลักโหราศาสตร์ไทยจากข้อมูลที่ให้มา โดยตอบให้ตรงคำถามและนำไปใช้ได้จริง
"""

        response = model.generate_content(system_instruction + "\n" + user_prompt)

        return {
            "zodiac": zodiac,
            "prediction": response.text,
            "status": "success",
            "transits": current_planets_data,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
