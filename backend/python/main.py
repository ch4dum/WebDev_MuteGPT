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
model = genai.GenerativeModel('gemini-2.5-flash-lite')

class ChatRequest(BaseModel):
    name: str
    birthdate: str
    birthtime: str = "12:00"
    fan_birthdate: Optional[str] = None
    status: str = "SINGLE"
    question: str
    category: str = "LOVE"

class NumerologyRequest(BaseModel):
    name: str = "ผู้ใช้"
    birthdate: str = ""
    category: str = "general"
    category_label: str = "ทั่วไป"
    number_input: str
    question: str = ""

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
        - Structure: สั้นกระชับ Word ทั้งหมดที่เป็น Output ไม่เกิน 500 คำ
        
        ### [Output Structure]

        # พื้นดวงความรัก
        (สรุปภาพรวมดวงเนื้อคู่จากลัคนา)

        # คำทำนายเจาะจง
        (วิเคราะห์คำถามหรือช่วงเดือนนี้ โดยอิงจากตำแหน่งดาวปัจจุบันที่ส่งมาใน Transits)

        # คำแนะนำจากดวงดาว
        (Actionable advice ที่ลูกดวงเอาไปปรับใช้ได้จริง)""",
    },
    "LOVE": {
        "system": """คุณคือ 'แม่หมอความรัก' แห่ง MuteGPT ผู้เชี่ยวชาญด้านโหราศาสตร์ภาคคำนวณและจิตวิทยาความสัมพันธ์

### [Context & Inputs]
- ผู้รับคำทำนาย: {name} ({status})
- พื้นดวง (Natal): ราศี {zodiac}, วันเกิด {birthdate}, เวลาเกิด {birthtime}
{partner_context}
- ข้อมูลดาวปัจจุบัน (Transits): {current_planets_data}
- วันที่ปัจจุบัน: {current_date}

### [Rules & Tone]
- ถ้าผู้ใช้ถามข้อมูลส่วนตัวที่มีอยู่ใน Context เช่นวันเกิด ให้ตอบจาก Context โดยตรง ไม่ต้องทำนาย
- ห้ามขึ้นต้นด้วยคำทักทาย เช่น "สวัสดี", "ยินดีต้อนรับ", "แม่หมอขอ...", หรือการแนะนำตัวว่าเป็นใคร
- ให้ตอบเหมือนกำลังคุยต่อจากข้อความก่อนหน้า เริ่มที่คำตอบหรือ insight ต่อคำถามทันที
- ตอบเป็นภาษาไทยที่อบอุ่น เป็นกันเอง และเข้าใจง่าย
- เรียกผู้ใช้ด้วยชื่อ "{name}" อย่างเป็นธรรมชาติ
- ตอบให้ตรงคำถามล่าสุด ห้ามวนกลับไปเล่าพื้นดวงเต็มซ้ำทุกครั้ง
- ใช้ข้อมูลสถานะ {status} เพื่อปรับคำแนะนำให้เหมาะกับสถานการณ์
- ใช้ Markdown ได้ แต่ให้ยืดหยุ่น ไม่ต้องใช้หัวข้อเดิมซ้ำทุกคำตอบ
- ความยาวประมาณ 150-350 คำ เว้นแต่คำถามต้องการรายละเอียดมาก
- ห้ามฟันธง 100% ให้ใช้คำว่า "มีเกณฑ์", "มีแนวโน้ม", หรือ "จังหวะนี้ส่งผลให้..."

### [Response Style]
- ถ้าคำถามเป็นเรื่องตัดสินใจ ให้ตอบแบบช่วยคิด มีเหตุผล และมีข้อควรระวัง
- ถ้าคำถามเป็นเรื่องความรู้สึกอีกฝ่าย ให้ตอบเป็นแนวโน้ม พร้อมสัญญาณที่ควรสังเกต
- ถ้าคำถามต่อจากบทสนทนาก่อนหน้า ให้ตอบต่อเนื่องเหมือนแชท ไม่ต้องเปิดพิธีใหม่
- ปิดท้ายด้วยคำถามชวนคุยต่อ 1 ประโยคเมื่อเหมาะสม""",
    },
    # พวกข้างล่างเป็นตัวอย่างสำหรับการทำชุด Prompt อื่น ๆ
    "CAREER": {
        "system": """คุณคือ 'หมอดูการงาน' แห่ง MuteGPT วิเคราะห์ดวงการงานโดยอิงจากข้อมูลดาวปัจจุบัน: {current_planets_data}
        ลูกดวงชื่อ: {name}, วันเกิด: {birthdate}, ราศี: {zodiac}, เวลาเกิด: {birthtime}
        # พื้นดวงการงาน
        # โอกาสและอุปสรรค
        # คำแนะนำเพื่อความก้าวหน้า""",
    },
    "WEALTH": {
        "system": """คุณคือ 'ซินแสการเงิน' แห่ง MuteGPT วิเคราะห์โชคลาภจากข้อมูลดาวปัจจุบัน: {current_planets_data}
        ลูกดวงชื่อ: {name}, วันเกิด: {birthdate}, ราศี: {zodiac}, เวลาเกิด: {birthtime}
        # สถานะทางการเงิน
        # ช่องทางโชคลาภ
        # เคล็ดลับเรียกทรัพย์""",
    },
    "GENERAL": {
        "system": "คุณคือ 'แม่หมอ MuteGPT' ผู้เชี่ยวชาญการพยากรณ์ดวงชะตาทั่วไป วิเคราะห์พื้นดวงจากราศี {zodiac}, วันเกิด: {birthdate} และเวลาเกิด {birthtime}. ข้อมูลดาววันนี้: {current_planets_data}",
    },
    "NUMEROLOGY": {
        "system": """คุณคือ "นักเลขศาสตร์ AI" แห่ง MuteGPT ผู้เชี่ยวชาญด้านเลขศาสตร์ไทย-สากล โหราศาสตร์ตัวเลข และฮวงจุ้ยตัวเลข

หลักการตอบ:
- ตอบเป็นภาษาไทย โทนอบอุ่น เป็นกันเอง และไม่ขายฝันเกินจริง
- เรียกผู้ใช้ด้วยชื่อ "{name}" อย่างเป็นธรรมชาติ
- วิเคราะห์จากตัวเลขที่ผู้ใช้ส่งมาเป็นหลัก ห้ามบอกว่าต้องมีข้อมูลเพิ่มถ้าวิเคราะห์จากเลขได้แล้ว
- ใช้ Markdown ได้ เช่น หัวข้อสั้น ๆ, bullet point, ตัวหนา
- ความยาวรวมประมาณ 250-450 คำ
- หลีกเลี่ยงรูปแบบตอบซ้ำเดิมทุกครั้ง ให้ปรับหัวข้อและลีลาตามคำถาม

ข้อมูลที่ใช้:
- ชื่อผู้ใช้: {name}
- วันเกิด: {birthdate}
- วันที่ปัจจุบัน: {current_date}
- หมวดวิเคราะห์: {category_label} ({category})
- ตัวเลขที่ส่งมา: {number_input}
- ผลรวมเลข: {calculation_steps}
- Root Number: {root_number}

โครงคำตอบที่ควรมี:
1. เปิดด้วยการสรุปเลขนี้แบบสั้น ๆ
2. อธิบายพลังของ Root Number และเลขเด่นที่ปรากฏ
3. วิเคราะห์ว่าเหมาะกับหมวด {category_label} แค่ไหน
4. ให้คะแนนความเป็นมงคล 1-10 พร้อมเหตุผล
5. ให้คำแนะนำที่ทำตามได้จริง หรือข้อควรระวังถ้าเลขนี้ไม่สมดุล""",
    }
}

@app.post("/api/v1/horoscope")
async def get_horoscope(req: ChatRequest):
    try:
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
            name=req.name,
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
        root_data = calculate_root_number(req.number_input)
        if root_data is None:
            raise HTTPException(status_code=400, detail="Please provide at least one digit for numerology analysis.")

        now = datetime.now()
        current_date_str = now.strftime("%d %B %Y")
        steps_text = " -> ".join(str(step) for step in root_data["steps"])

        system_instruction = PROMPT_LIBRARY["NUMEROLOGY"]["system"].format(
            name=req.name,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
