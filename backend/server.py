from fastapi import FastAPI, APIRouter, HTTPException, Header, Depends, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import secrets
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
# pymongo 4.x + motor 3.x handle TLS automatically via the SRV connection
# string — passing tlsCAFile explicitly conflicts with the driver's internal
# certificate handling and causes TLSV1_ALERT_INTERNAL_ERROR on Atlas.
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Admin token: no insecure hardcoded fallback ---
# If ADMIN_TOKEN isn't set in .env, generate a random one for this run and log it,
# instead of shipping a publicly-known default that anyone reading the source could use.
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN')
if not ADMIN_TOKEN:
    ADMIN_TOKEN = secrets.token_urlsafe(24)
    logger.warning(
        "ADMIN_TOKEN not set in .env — generated a temporary one for this run: %s\n"
        "Set ADMIN_TOKEN in backend/.env to persist a stable admin token across restarts.",
        ADMIN_TOKEN,
    )

app = FastAPI(title="PromptPop API")
api_router = APIRouter(prefix="/api")


# ---------- Models ----------
class PromptCardBase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    style: str                       # Lo-Fi, Cyberpunk, Y2K, Cinematic, Dreamy Pastel, etc.
    vibe: str                        # short descriptor e.g. "Phone-shot, soft focus"
    use_case: str                    # Portrait, Product, Thumbnail, Quote, Story, etc.
    platforms: List[str] = []        # TikTok, Instagram, YouTube, Pinterest, etc.
    hotness: int = 4                 # 1-5
    prompt_text: str                 # The copy-paste prompt
    reference_image_url: str = ""    # URL of reference style image
    reference_guidelines: str = ""   # What kind of image user should upload
    tags: List[str] = []             # Hashtags
    aspect_ratio: str = "9:16"
    duration: str = ""               # For video prompts, e.g. "5-8s"
    remix_tips: List[str] = []       # List of remix suggestion strings
    micro_badges: List[str] = []     # Trending, Viral, Quick Remix, Premium Look
    signature_color: str = ""        # Optional override for style color


class PromptCard(PromptCardBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PromptCardCreate(PromptCardBase):
    pass


class PromptCardUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    style: Optional[str] = None
    vibe: Optional[str] = None
    use_case: Optional[str] = None
    platforms: Optional[List[str]] = None
    hotness: Optional[int] = None
    prompt_text: Optional[str] = None
    reference_image_url: Optional[str] = None
    reference_guidelines: Optional[str] = None
    tags: Optional[List[str]] = None
    aspect_ratio: Optional[str] = None
    duration: Optional[str] = None
    remix_tips: Optional[List[str]] = None
    micro_badges: Optional[List[str]] = None
    signature_color: Optional[str] = None


def _serialize(card_dict: dict) -> dict:
    """Convert datetimes to ISO strings for storage."""
    out = dict(card_dict)
    for k in ("created_at", "updated_at"):
        if isinstance(out.get(k), datetime):
            out[k] = out[k].isoformat()
    return out


def _deserialize(doc: dict) -> dict:
    """Parse datetimes back from ISO strings."""
    out = dict(doc)
    out.pop("_id", None)
    for k in ("created_at", "updated_at"):
        if isinstance(out.get(k), str):
            try:
                out[k] = datetime.fromisoformat(out[k])
            except ValueError:
                pass
    return out


def require_admin(x_admin_token: Optional[str] = Header(None)):
    if not x_admin_token or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return True


# ---------- Seed data ----------
SEED_CARDS: List[dict] = [
    {
        "name": "Lo-Fi Real Life Portrait",
        "style": "Lo-Fi",
        "vibe": "Candid, phone-shot, grainy authenticity",
        "use_case": "Portrait",
        "platforms": ["Instagram", "TikTok"],
        "hotness": 5,
        "prompt_text": "A candid portrait of [describe subject] in a real-life moment, soft natural light, shot on a phone camera, slightly overexposed, visible film grain, subtle blur, warm color tones, no heavy filters, looks like a real unedited photo, 4K detail.",
        "reference_image_url": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&q=80",
        "reference_guidelines": "Upload a regular selfie or casual portrait (not too posed). Frame: face and upper body, natural background (room, street, café).",
        "tags": ["#lofi", "#realmoment", "#unfiltered", "#aesthetic", "#photoDump"],
        "aspect_ratio": "4:5",
        "duration": "",
        "remix_tips": [
            "Change 'soft natural light' to 'neon light' or 'golden hour' for different moods.",
            "Replace 'candid portrait' with 'two friends laughing in a café' for more story."
        ],
        "micro_badges": ["Trending", "Quick Remix"],
        "signature_color": "#FFCBA4"
    },
    {
        "name": "Cyberpunk Neon Street Shot",
        "style": "Cyberpunk",
        "vibe": "Rain-soaked neon, cinematic, electric",
        "use_case": "Thumbnail",
        "platforms": ["TikTok", "YouTube"],
        "hotness": 5,
        "prompt_text": "A cinematic wide shot of [you or your character] standing in a rain-soaked cyberpunk street at midnight, neon signs reflecting on wet pavement, blue and magenta color palette, dramatic backlighting, ultra-detailed, looks like a movie still.",
        "reference_image_url": "https://images.unsplash.com/photo-1480796927426-f609979314bd?w=800&q=80",
        "reference_guidelines": "Upload full-body or half-body photo, preferably standing. Background doesn't matter; the model will replace it with the city scene.",
        "tags": ["#cyberpunk", "#aiart", "#neoncity", "#futurevibes", "#gamer"],
        "aspect_ratio": "16:9",
        "duration": "",
        "remix_tips": [
            "Swap colors: 'orange and teal' instead of 'blue and magenta'.",
            "Change mood: 'mysterious and lonely' to 'energetic and crowded'."
        ],
        "micro_badges": ["Viral", "Premium Look"],
        "signature_color": "#FF00FF"
    },
    {
        "name": "Y2K Chrome Pop Portrait",
        "style": "Y2K",
        "vibe": "Glossy chrome, bubblegum, early-internet pop",
        "use_case": "Portrait",
        "platforms": ["Instagram", "TikTok"],
        "hotness": 4,
        "prompt_text": "A Y2K-inspired digital portrait of [you or your character], chrome metallic highlights on skin, holographic background, bubblegum pink and silver color palette, glossy plastic accessories, early 2000s pop star energy, vibrant and synthetic.",
        "reference_image_url": "https://images.unsplash.com/photo-1496440737103-cd596325d314?w=800&q=80",
        "reference_guidelines": "Upload a close-up selfie with clear face. Confident, playful expression works best.",
        "tags": ["#y2k", "#aesthetic", "#chrome", "#aiavatar", "#popvibes"],
        "aspect_ratio": "1:1",
        "duration": "",
        "remix_tips": [
            "Swap 'bubblegum pink' for 'electric blue' for a different palette.",
            "Add text layer later: 'New Drop', 'Coming Soon', etc."
        ],
        "micro_badges": ["Trending"],
        "signature_color": "#A0D8EF"
    },
    {
        "name": "Cinematic Film Still",
        "style": "Cinematic",
        "vibe": "High-contrast prestige movie frame",
        "use_case": "Thumbnail",
        "platforms": ["YouTube", "Instagram"],
        "hotness": 5,
        "prompt_text": "A dramatic cinematic close-up of [subject] in the middle of an intense moment, shallow depth of field, background softly blurred, high contrast lighting, subtle film grain, looks like a frame from a prestige movie, 4K.",
        "reference_image_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&q=80",
        "reference_guidelines": "Upload a close-up with strong emotion (laughing, shocked, excited) for maximum drama.",
        "tags": ["#cinematic", "#filmstill", "#storytime", "#vlogvibes"],
        "aspect_ratio": "16:9",
        "duration": "",
        "remix_tips": [
            "Change emotion: 'on the verge of laughing', 'about to cry', 'shocked reaction'.",
            "Add text in bold blocks: 'I QUIT', 'HOW I DID IT', etc."
        ],
        "micro_badges": ["Premium Look", "Viral"],
        "signature_color": "#FFBF00"
    },
    {
        "name": "Dreamy Pastel Surreal Scene",
        "style": "Dreamy Pastel",
        "vibe": "Floating, soft, calming surrealism",
        "use_case": "Product",
        "platforms": ["Pinterest", "Instagram"],
        "hotness": 4,
        "prompt_text": "A dreamy pastel surreal scene of [subject or object], soft pink, lavender and baby blue color palette, floating elements around, soft diffused lighting, gentle and calming mood, high resolution.",
        "reference_image_url": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=800&q=80",
        "reference_guidelines": "Upload either a product shot (skincare, candle, notebook) or a simple portrait.",
        "tags": ["#pastel", "#surreal", "#calmvibes", "#selfcare", "#aestheticfeed"],
        "aspect_ratio": "4:5",
        "duration": "",
        "remix_tips": [
            "Swap colors: 'mint green and cream' or 'sunset orange and peach'.",
            "Change objects: from 'floating petals' to 'floating icons related to your niche'."
        ],
        "micro_badges": ["Quick Remix"],
        "signature_color": "#E6E6FA"
    },
    {
        "name": "Anime Cel Shaded Hero",
        "style": "Anime",
        "vibe": "Bold cel-shading, manga panel energy",
        "use_case": "Avatar",
        "platforms": ["TikTok", "Twitter"],
        "hotness": 4,
        "prompt_text": "An anime cel-shaded portrait of [subject] in a dynamic hero pose, bold black outlines, vivid flat colors, dramatic speed lines in the background, manga panel composition, studio-quality finish.",
        "reference_image_url": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800&q=80",
        "reference_guidelines": "Upload a clear portrait. Looking up or sideways works best for dynamic hero vibes.",
        "tags": ["#anime", "#aiavatar", "#manga", "#celshaded", "#otaku"],
        "aspect_ratio": "9:16",
        "duration": "",
        "remix_tips": [
            "Swap setting to 'futuristic city skyline' or 'training arena'.",
            "Add weapon, magic aura, or signature accessory for character identity."
        ],
        "micro_badges": ["Trending", "Quick Remix"],
        "signature_color": "#FFD166"
    },
    {
        "name": "SaaS Founder Office Hero",
        "style": "Cinematic",
        "vibe": "Editorial, founder-mode, magazine cover",
        "use_case": "LinkedIn / Headshot",
        "platforms": ["LinkedIn", "Twitter"],
        "hotness": 4,
        "prompt_text": "An editorial magazine portrait of [subject] in a minimalist modern office, soft window light, looking confidently off-camera, 35mm photography, sharp focus on subject, slightly desaturated tones, looks like a Forbes cover.",
        "reference_image_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=800&q=80",
        "reference_guidelines": "Upload a clean shoulders-up photo. Neutral or solid color top works best.",
        "tags": ["#founder", "#startup", "#linkedin", "#buildinpublic", "#saas"],
        "aspect_ratio": "4:5",
        "duration": "",
        "remix_tips": [
            "Swap 'minimalist modern office' for 'warehouse studio' or 'rooftop at golden hour'.",
            "Change publication: 'Bloomberg cover', 'Wired editorial', 'TIME magazine'."
        ],
        "micro_badges": ["Premium Look"],
        "signature_color": "#FFBF00"
    },
    {
        "name": "Fashion Lookbook Studio",
        "style": "Y2K",
        "vibe": "High-fashion catalog, bold backdrops",
        "use_case": "Product",
        "platforms": ["Instagram", "Pinterest"],
        "hotness": 4,
        "prompt_text": "A high-fashion lookbook shot of [subject] wearing [outfit description], standing against a saturated solid color backdrop, studio lighting with hard shadow, looking directly at the camera, Vogue editorial aesthetic.",
        "reference_image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=800&q=80",
        "reference_guidelines": "Upload a full-body or half-body photo. Plain background preferred.",
        "tags": ["#fashion", "#lookbook", "#editorial", "#aesthetic", "#ootd"],
        "aspect_ratio": "4:5",
        "duration": "",
        "remix_tips": [
            "Change backdrop color to match your brand palette.",
            "Add 'inspired by Jacquemus / Mugler / Bottega' for designer style cues."
        ],
        "micro_badges": ["Premium Look", "Trending"],
        "signature_color": "#A0D8EF"
    },
    {
        "name": "Gamer Stream Banner",
        "style": "Cyberpunk",
        "vibe": "Twitch-ready, dramatic, gamer-core",
        "use_case": "Thumbnail",
        "platforms": ["YouTube", "Twitch"],
        "hotness": 4,
        "prompt_text": "A dramatic banner of [subject] in a gaming setup, RGB keyboard glow, dual monitors, dark room with purple and cyan ambient lighting, shallow depth of field, intense gaming face, cinematic widescreen composition.",
        "reference_image_url": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800&q=80",
        "reference_guidelines": "Upload a half-body photo, headset optional. Background will be replaced.",
        "tags": ["#gaming", "#twitch", "#streamer", "#rgb", "#esports"],
        "aspect_ratio": "16:9",
        "duration": "",
        "remix_tips": [
            "Swap colors: 'red and orange aggressive vibe', 'green hacker vibe'.",
            "Add game-specific elements: 'Valorant agent silhouette', 'Minecraft block accents'."
        ],
        "micro_badges": ["Viral", "Quick Remix"],
        "signature_color": "#FF00FF"
    },
    {
        "name": "Calm Quote Card",
        "style": "Dreamy Pastel",
        "vibe": "Wellness, breathable, journal-coded",
        "use_case": "Quote",
        "platforms": ["Pinterest", "Instagram"],
        "hotness": 3,
        "prompt_text": "A minimal pastel background with hand-drawn organic shapes, beige and sage palette, soft paper texture, space in the center for a calming quote, journal aesthetic, breathable composition.",
        "reference_image_url": "https://images.unsplash.com/photo-1490598000245-075175152d25?w=800&q=80",
        "reference_guidelines": "No subject needed. Pure background generator; add your text in Canva after.",
        "tags": ["#quote", "#mindful", "#selfcare", "#pinterest", "#wellness"],
        "aspect_ratio": "4:5",
        "duration": "",
        "remix_tips": [
            "Swap palette to 'terracotta + cream' or 'navy + cream' to match your feed.",
            "Add 'tiny mountain illustration' or 'minimal sun arc' for variety."
        ],
        "micro_badges": ["Quick Remix"],
        "signature_color": "#E6E6FA"
    },
    {
        "name": "Music Artist Cover Drop",
        "style": "Cinematic",
        "vibe": "Album cover energy, single drop hype",
        "use_case": "Cover Art",
        "platforms": ["Spotify", "Instagram"],
        "hotness": 5,
        "prompt_text": "A moody cinematic cover art of [artist] photographed under a single hard spotlight, smoke in the air, deep blacks, single accent color light (red/blue/amber) on the face, looks like an album cover, square format.",
        "reference_image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800&q=80",
        "reference_guidelines": "Upload a close-up portrait. Neutral expression or looking down works best.",
        "tags": ["#newmusic", "#coverart", "#spotify", "#singer", "#newrelease"],
        "aspect_ratio": "1:1",
        "duration": "",
        "remix_tips": [
            "Switch accent color to match your single mood (red=passion, blue=melancholy).",
            "Add overlay text: track title in bold uppercase."
        ],
        "micro_badges": ["Trending", "Premium Look"],
        "signature_color": "#FFBF00"
    },
    {
        "name": "Phone-Shot Café Reel",
        "style": "Lo-Fi",
        "vibe": "Soft mornings, vlog energy, b-roll",
        "use_case": "Reel B-roll",
        "platforms": ["Instagram", "TikTok"],
        "hotness": 4,
        "prompt_text": "A handheld phone-shot b-roll clip of [subject] in a cozy café, soft window light, slow pour of coffee, gentle camera shake, warm tones, looks unedited, 5 second loop.",
        "reference_image_url": "https://images.unsplash.com/photo-1453614512568-c4024d13c247?w=800&q=80",
        "reference_guidelines": "Upload a video frame or photo of café interior; subject hand-only is fine.",
        "tags": ["#vlog", "#broll", "#cafe", "#aesthetic", "#dayinmylife"],
        "aspect_ratio": "9:16",
        "duration": "5-8s",
        "remix_tips": [
            "Swap café for 'bookstore', 'park bench', 'studio desk' to match your niche.",
            "Change time: 'late evening warm tones' for a moodier feel."
        ],
        "micro_badges": ["Quick Remix", "Trending"],
        "signature_color": "#FFCBA4"
    }
]
# NOTE: the 5 cards originally using Emergent-CDN-hosted reference images
# (Lo-Fi, Cyberpunk, Y2K, Cinematic, Dreamy Pastel) have been switched to
# stable Unsplash URLs above, since the original images were hosted on
# Emergent's job-specific CDN and would not survive outside that environment.
# Swap these for your own generated/uploaded images via the admin panel any time.


@app.on_event("startup")
async def seed_if_empty():
    """Insert seed cards only if collection is empty (idempotent)."""
    try:
        count = await db.prompt_cards.count_documents({})
        if count == 0:
            now = datetime.now(timezone.utc).isoformat()
            docs = []
            for c in SEED_CARDS:
                card = PromptCard(**c)
                d = _serialize(card.model_dump())
                d["created_at"] = now
                d["updated_at"] = now
                docs.append(d)
            await db.prompt_cards.insert_many(docs)
            logger.info(f"Seeded {len(docs)} prompt cards.")
    except Exception as e:
        logger.error(f"Seed error: {e}")


# ---------- Routes ----------
@api_router.get("/")
async def root():
    return {"message": "PromptPop API ready"}


@api_router.get("/prompts", response_model=List[PromptCard])
async def list_prompts(
    style: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    use_case: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query("hotness"),
):
    query: dict = {}
    if style and style.lower() != "all":
        query["style"] = style
    if platform and platform.lower() != "all":
        query["platforms"] = platform
    if use_case and use_case.lower() != "all":
        query["use_case"] = use_case
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"vibe": {"$regex": search, "$options": "i"}},
            {"prompt_text": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}},
        ]

    sort_field = "hotness" if sort == "hotness" else "created_at"
    cursor = db.prompt_cards.find(query, {"_id": 0}).sort(sort_field, -1)
    docs = await cursor.to_list(500)
    return [PromptCard(**_deserialize(d)) for d in docs]


@api_router.get("/prompts/meta")
async def get_meta():
    docs = await db.prompt_cards.find({}, {"_id": 0, "style": 1, "platforms": 1, "use_case": 1}).to_list(1000)
    styles = sorted({d.get("style") for d in docs if d.get("style")})
    use_cases = sorted({d.get("use_case") for d in docs if d.get("use_case")})
    platforms = sorted({p for d in docs for p in (d.get("platforms") or [])})
    return {"styles": list(styles), "platforms": list(platforms), "use_cases": list(use_cases)}


@api_router.get("/prompts/{prompt_id}", response_model=PromptCard)
async def get_prompt(prompt_id: str):
    doc = await db.prompt_cards.find_one({"id": prompt_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return PromptCard(**_deserialize(doc))


@api_router.post("/prompts", response_model=PromptCard)
async def create_prompt(input: PromptCardCreate, _: bool = Depends(require_admin)):
    card = PromptCard(**input.model_dump())
    doc = _serialize(card.model_dump())
    await db.prompt_cards.insert_one(doc)
    return card


@api_router.put("/prompts/{prompt_id}", response_model=PromptCard)
async def update_prompt(prompt_id: str, input: PromptCardUpdate, _: bool = Depends(require_admin)):
    existing = await db.prompt_cards.find_one({"id": prompt_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.prompt_cards.update_one({"id": prompt_id}, {"$set": update_data})
    doc = await db.prompt_cards.find_one({"id": prompt_id}, {"_id": 0})
    return PromptCard(**_deserialize(doc))


@api_router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str, _: bool = Depends(require_admin)):
    res = await db.prompt_cards.delete_one({"id": prompt_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"deleted": True, "id": prompt_id}


@api_router.post("/admin/verify")
async def verify_admin(_: bool = Depends(require_admin)):
    return {"ok": True}


app.include_router(api_router)

cors_origins = os.environ.get("CORS_ORIGINS")
if cors_origins:
    allowed_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
else:
    allowed_origins = [
        "https://trendyprompts.vercel.app/",
        "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
