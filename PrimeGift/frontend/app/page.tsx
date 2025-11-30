// ... (Interface Case needs optional field last_opened)
interface Case {
  id: number;
  name: string;
  image_url: string;
  price: number;
  currency: string;
  is_limited: boolean;
  limit_total?: number;
  limit_remaining?: number;
}

// ... (In User interface)
interface User {
  // ...
  last_daily_spin?: string; // ISO date
}

// ... (In CasesView)
function CasesView({ cases, onOpen, user }: { cases: Case[], onOpen: (id: number) => void, user: User | null }) {
    const limitedCases = cases.filter(c => c.is_limited);
    const regularCases = cases.filter(c => !c.is_limited);

    return (
        <div className="px-4 pt-6 space-y-8 animate-in fade-in duration-500">
            {/* Limited Section */}
            {limitedCases.length > 0 && (
                <div>
                    <div className="flex justify-between items-end mb-3">
                        <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-2">
                            <Clock className="w-3 h-3" /> Лимитированные
                        </h3>
                        <span className="text-[10px] text-red-400 font-mono animate-pulse">Успей забрать!</span>
                    </div>
                    <div className="space-y-4">
                        {limitedCases.map(c => (
                            <LimitedCaseCard key={c.id} data={c} onOpen={() => onOpen(c.id)} />
                        ))}
                    </div>
                </div>
            )}

            {/* Regular Section */}
            <div>
                <h3 className="text-xs font-bold text-zinc-500 mb-3 uppercase tracking-wider">Бесплатные и Обычные</h3>
                <div className="space-y-3">
                    {regularCases.map(c => (
                        <CaseCard key={c.id} title={c.name} image={c.image_url} glow="blue" user={user} onOpen={() => onOpen(c.id)} />
                    ))}
                </div>
            </div>
        </div>
    )
}

// ... (In Home component, pass user to CasesView)
// {activeTab === "cases" && <CasesView cases={cases} onOpen={openCase} user={user} />}

// ... (In CaseCard)
function CaseCard({ title, subtitle, image, glow, user, onOpen }: any) {
    const glows: any = {
        blue: "shadow-blue-900/20 border-blue-500/20 from-blue-950/40 to-zinc-900",
        purple: "shadow-purple-900/20 border-purple-500/20 from-purple-950/40 to-zinc-900"
    };
    
    const isFree = title.toLowerCase().includes("бесплатн") || title.toLowerCase().includes("ежедневн");
    
    // Timer Logic
    const [timeLeft, setTimeLeft] = useState<string | null>(null);
    
    useEffect(() => {
        if (isFree && user?.last_daily_spin) {
            const checkTime = () => {
                const lastSpin = new Date(user.last_daily_spin).getTime();
                const now = new Date().getTime();
                const diff = now - lastSpin;
                const cooldown = 24 * 60 * 60 * 1000;
                
                if (diff < cooldown) {
                    const remaining = cooldown - diff;
                    const h = Math.floor((remaining / (1000 * 60 * 60)) % 24);
                    const m = Math.floor((remaining / (1000 * 60)) % 60);
                    const s = Math.floor((remaining / 1000) % 60);
                    setTimeLeft(`${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`);
                } else {
                    setTimeLeft(null);
                }
            };
            
            checkTime();
            const interval = setInterval(checkTime, 1000);
            return () => clearInterval(interval);
        }
    }, [user?.last_daily_spin, isFree]);

    const handleClick = () => {
        if (timeLeft) return;
        if (onOpen) onOpen();
    };

    return (
        <div className={`w-full h-40 rounded-3xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] bg-gradient-to-r ${glows[glow]} border`}>
            {/* ... (Backgrounds same) ... */}
            <div className={`absolute -left-10 -top-10 w-40 h-40 blur-[60px] rounded-full opacity-20 ${glow === 'blue' ? 'bg-blue-500' : 'bg-purple-500'}`}></div>
            <div className="flex h-full relative z-10 bg-zinc-950/40 backdrop-blur-sm p-0 gap-4">
                <div className="w-44 h-full flex-shrink-0 relative flex items-center justify-center -ml-2">
                     <img 
                        src={image} 
                        alt={title} 
                        className="w-full h-[130%] object-contain drop-shadow-2xl transition-transform group-hover:scale-110 group-hover:rotate-2" 
                     />
                </div>
                <div className="flex flex-col justify-center flex-1 py-4 pr-5">
                    <div className="mb-3 text-right">
                        <h3 className="font-black text-2xl text-white leading-none tracking-tight uppercase italic">{title}</h3>
                        {subtitle && subtitle !== "ХАЛЯВА" && (
                            <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest opacity-70">
                                {subtitle}
                            </span>
                        )}
                    </div>
                    
                    <button 
                        onClick={handleClick}
                        disabled={!!timeLeft}
                        className={`w-full relative group overflow-hidden rounded-xl transition-all duration-300 ${!!timeLeft ? 'cursor-not-allowed grayscale opacity-70' : 'hover:shadow-[0_0_20px_rgba(56,189,248,0.6)] active:scale-95'}`}
                    >
                        {/* Background logic */}
                        <div className={`absolute inset-0 bg-gradient-to-b ${isFree ? 'from-sky-400 via-sky-500 to-blue-600' : 'from-amber-300 via-amber-500 to-amber-600'}`}></div>
                        <div className="absolute inset-0 opacity-20 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]"></div>
                        <div className="absolute top-0 left-0 right-0 h-[40%] bg-gradient-to-b from-white/50 to-transparent"></div>
                        
                        <div className="relative py-3.5 px-4 flex items-center justify-center gap-2 z-10">
                           {timeLeft ? (
                               <span className="font-mono font-bold text-white text-sm drop-shadow-md tracking-wider">{timeLeft}</span>
                           ) : (
                               <>
                                   <Gift className="w-4 h-4 text-white drop-shadow-md animate-bounce" />
                                   <span className="font-black text-white text-sm tracking-widest drop-shadow-md uppercase">
                                       {isFree ? 'БЕСПЛАТНО' : 'ОТКРЫТЬ'}
                                   </span>
                               </>
                           )}
                        </div>
                        <div className="absolute inset-0 border border-white/30 rounded-xl pointer-events-none"></div>
                    </button>
                </div>
            </div>
        </div>
    )
}
