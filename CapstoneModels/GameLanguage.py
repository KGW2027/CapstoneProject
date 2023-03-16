
def remove(text: str):
    return text.replace("'", "").replace("\"", "").replace(",", "")

def replace(text: str):
    text = remove(text.lower())
    for eng, ko in get_dict().items():
        # 짧은 이름의 경우 한 단어에 포함되어 있을 수 있다. ( 일반적으로 영어가 남아 있는 경우가 잘못됬다고 볼 수 있지만 )
        # 이 경우를 대비하기 위해, 뒤에는 조사가 올 수 있지만 앞에는 아무 글자가 없는게 일반적이므로, 앞에 [Sp]를 포함한다.
        text = text.replace(" " + eng, " " + ko)
        # 번역 옮기기 과정에서 첫 글자가 사라졌을 가능성이 있으므로, 이를 반영함 (단 vi의 경우 오번역 가능성이 높아 제외함)
        if eng != "vi":
            text = text.replace(" " + eng[1:], " " + ko)
    return text

def get_dict():
    return {
        # 캐릭터명
        "aatrox":"아트록스",
        "ahri":"아리",
        "akali":"아칼리",
        "akshan":"아크샨",
        "alistar":"알리스타",
        "amumu":"아무무",
        "anivia":"애니비아",
        "annie":"애니",
        "aphelios":"아펠리오스",
        "ashe":"애쉬",
        "aurelion-sol":"아우렐리온-솔",
        "azir":"아지르",
        "bard":"바드",
        "bel-veth":"벨베스",
        "blitzcrank":"블리츠크랭크",
        "brand":"브랜드",
        "braum":"브라움",
        "caitlyn":"케이틀린",
        "camille":"카밀",
        "cassiopeia":"카시오페아",
        "cho-gath":"초가스",
        "corki":"코르키",
        "darius":"다리우스",
        "diana":"다이애나",
        "dr-mundo":"문도박사",
        "draven":"드레이븐",
        "ekko":"에코",
        "elise":"엘리스",
        "evelynn":"이블린",
        "ezreal":"이즈리얼",
        "fiddlesticks":"피들스틱",
        "fiora":"피오라",
        "fizz":"피즈",
        "galio":"갈리오",
        "gangplank":"갱플랭크",
        "garen":"가렌",
        "gnar":"나르",
        "gragas":"그라가스",
        "graves":"그레이브즈",
        "gwen":"그웬",
        "hecarim":"헤카림",
        "heimerdinger":"하이머딩거",
        "illaoi":"일라오이",
        "irelia":"이렐리아",
        "ivern":"아이번",
        "janna":"잔나",
        "jarvan-iv":"자르반4세",
        "jax":"잭스",
        "jayce":"제이스",
        "jhin":"진",
        "jinx":"징크스",
        "k-sante":"크산테",
        "kai-sa":"카이사",
        "kalista":"칼리스타",
        "karma":"카르마",
        "karthus":"카서스",
        "kassadin":"카사딘",
        "katarina":"카타리나",
        "kayle":"케일",
        "kayn":"케인",
        "kennen":"케넨",
        "kha-zix":"카직스",
        "kindred":"킨드레드",
        "kled":"크레드",
        "kog-maw":"코그모",
        "leblanc":"르블랑",
        "lee-sin":"리신",
        "leona":"레오나",
        "lillia":"릴리아",
        "lissandra":"리산드라",
        "lucian":"루시안",
        "lulu":"룰루",
        "lux":"럭스",
        "malphite":"말파이트",
        "malzahar":"말자하",
        "maokai":"마오카이",
        "master-yi":"마스터이",
        "miss-fortune":"미스포춘",
        "mordekaiser":"모데카이저",
        "morgana":"모르가나",
        "nami":"나미",
        "nasus":"나서스",
        "nautilus":"노틸러스",
        "neeko":"니코",
        "nidalee":"니달리",
        "nilah":"닐라",
        "nocturne":"녹턴",
        "nunu":"누누",
        "olaf":"올라프",
        "orianna":"오리아나",
        "ornn":"오른",
        "pantheon":"판테온",
        "poppy":"뽀삐",
        "pyke":"파이크",
        "qiyana":"키아나",
        "quinn":"퀸",
        "rakan":"라칸",
        "rammus":"람머스",
        "rek-sai":"렉사이",
        "rell":"렐",
        "renata":"레나타",
        "renekton":"레넥톤",
        "rengar":"렝가",
        "riven":"리븐",
        "rumble":"럼블",
        "ryze":"라이즈",
        "samira":"사미라",
        "sejuani":"세주아니",
        "senna":"세나",
        "seraphine":"세라핀",
        "sett":"세트",
        "shaco":"샤코",
        "shen":"쉔",
        "shyvana":"쉬바나",
        "singed":"신지드",
        "sion":"사이온",
        "sivir":"시비르",
        "skarner":"스카너",
        "sona":"소나",
        "soraka":"소라카",
        "swain":"스웨인",
        "sylas":"사일러스",
        "syndra":"신드라",
        "tahm-kench":"탐켄치",
        "taliyah":"탈리야",
        "talon":"탈론",
        "taric":"타릭",
        "teemo":"티모",
        "thresh":"쓰레쉬",
        "tristana":"트리스타나",
        "trundle":"트런들",
        "tryndamere":"트린다미어",
        "twisted-fate":"트위스티드페이트",
        "twitch":"트위치",
        "udyr":"우디르",
        "urgot":"우르곳",
        "varus":"바루스",
        "vayne":"베인",
        "veigar":"베이가",
        "vel-koz":"벨코즈",
        "vex":"벡스",
        "viego":"비에고",
        "vi":"바이",
        "viktor":"빅토르",
        "vladimir":"블라디미르",
        "volibear":"볼리베어",
        "warwick":"워윅",
        "wukong":"오공",
        "xayah":"자야",
        "xerath":"제라스",
        "xin-zhao":"신짜오",
        "yasuo":"야스오",
        "yone":"요네",
        "yorick":"요릭",
        "yuumi":"유미",
        "zac":"자크",
        "zed":"제드",
        "zeri":"제리",
        "ziggs":"직스",
        "zilean":"질리언",
        "zoe":"조이",
        "zyra":"자이라",
        
        # 지명
        "runeterra": "룬테라",
        "valoran": "발로란",
        "bandlecity": "밴들시티",
        "bilgewater": "빌지워터",
        "demacia": "데마시아",
        "ionia": "아이오니아",
        "ixtal": "이쉬탈",
        "noxus": "녹서스",
        "piltover": "필트오버",
        "shadowisles": "그림자군도",
        "shurima": "슈리마",
        "targon": "타곤",
        "freljord": "프렐요드",
        "void": "공허",
        "zaun": "자운"
        
            }