"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { Star, Hexagon, Gift, Users, Zap, Swords, Sparkles, ChevronRight, Copy, Settings, Trophy, Skull, Clock, Home as HomeIcon, X, Info, Ticket as TicketIcon } from "lucide-react";
import axios from "axios";

// --- CONFIGURATION ---
// HARDCODED API URL
const API_URL = "https://motivated-comfort-production.up.railway.app";

interface User {
  id: number;
  username: string;
  balance_stars: number;
  balance_tickets: number;
  photo_url?: string;
  referral_code?: string;
  subscription_reward_claimed?: boolean;
  referrals_count?: number;
  is_admin?: boolean;
}

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

// Tab names changed to reflect new structure
type Tab = "home" | "upgrade" | "cases" | "arena" | "profile";

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("home"); 
  const [cases, setCases] = useState<Case[]>([]);
  
  // Modal State
  const [showInfoModal, setShowInfoModal] = useState(false);
  
  // Promo Modal State
  const [showPromoModal, setShowPromoModal] = useState(false);
  const [promoCodeInput, setPromoCodeInput] = useState("");
  const [selectedFreeCaseId, setSelectedFreeCaseId] = useState<number | null>(null);
  
  // Animation State
  const [isOpening, setIsOpening] = useState(false);
  const [openingCaseId, setOpeningCaseId] = useState<number | null>(null);
  const [wonItem, setWonItem] = useState<any>(null);
  const [showRewardModal, setShowRewardModal] = useState(false);
  
  // Tasks State
  const [subTaskStatus, setSubTaskStatus] = useState<'go' | 'check' | 'done'>('go');

  const handleCheckSubscription = async () => {
      if (subTaskStatus === 'go') {
          if (window.Telegram?.WebApp) {
               window.Telegram.WebApp.openTelegramLink("https://t.me/TGiftPrime");
          } else {
               window.open("https://t.me/TGiftPrime", "_blank");
          }
          setSubTaskStatus('check');
      } else if (subTaskStatus === 'check') {
          // Call API
          try {
              // API_URL is global now
              // We need initData for check. Assuming we have user or can send empty if demo.
              // Better to use current initData from WebApp if available, but we don't store it in state.
              // Let's just simulate success for demo or try call.
              const tg = window.Telegram?.WebApp;
              const res = await axios.post(`${API_URL}/api/users/check-subscription`, { 
                  initData: tg?.initData || "demo", 
                  referrer_code: null 
              });
              
              if (res.data.subscribed) {
                  setSubTaskStatus('done');
                  if (res.data.just_rewarded) {
                      setUser(prev => prev ? ({ ...prev, balance_tickets: res.data.new_balance }) : null);
                      if (tg) tg.showPopup({ title: 'Успех!', message: 'Награда получена: 1 Купон' });
                  } else {
                      if (tg) tg.showPopup({ title: 'Успех!', message: 'Вы уже подписаны. Награда уже была получена.' });
                  }
              } else {
                  if (tg) tg.showPopup({ title: 'Ошибка', message: 'Вы не подписаны на канал!' });
              }
          } catch (e) {
              console.error(e);
              // Demo fallback
              setSubTaskStatus('done');
              setUser(prev => prev ? ({ ...prev, balance_tickets: prev.balance_tickets + 1 }) : null);
          }
      }
  };

  // --- INIT APP ---
  useEffect(() => {
    let mounted = true;
    const initApp = async () => {
      // PREMIUM DELAY: 2500ms for users to enjoy the loader
      await new Promise(resolve => setTimeout(resolve, 2500));
      if (!mounted) return;

      const tg = typeof window !== "undefined" && window.Telegram?.WebApp;
      
      if (tg?.initData) {
        tg.ready(); 
        tg.expand();
        try { tg.requestFullscreen(); } catch (e) {} // Force Fullscreen for mobile
        tg.setHeaderColor("#05050a"); // Match new background
        tg.setBackgroundColor("#05050a");
        try {
          // API_URL is global now
          const startParam = tg.initDataUnsafe?.start_param;
          
          const res = await axios.post(`${API_URL}/api/users/auth`, { 
              initData: tg.initData,
              referrer_code: startParam 
          }, { timeout: 5000 });
          
          if (mounted) setUser(res.data);

          const casesRes = await axios.get(`${API_URL}/api/cases/`, { timeout: 5000 });
          if (mounted) setCases(casesRes.data);

        } catch (e: any) {
          console.error("Init error:", e);
          if (mounted) {
             // --- DEBUG ALERT ---
             // Показываем ошибку пользователю, чтобы понять причину "Гостя"
             let errorMsg = "Connection Error";
             if (axios.isAxiosError(e)) {
                 errorMsg = `API Error: ${e.message}`;
                 if (e.response) errorMsg += ` (${e.response.status})`;
             }
             if (tg) tg.showAlert(`Ошибка входа: ${errorMsg}\nURL: ${API_URL}`);
             
             if (!user) setUser({ id: 0, username: "Guest", balance_stars: 0, balance_tickets: 0 });
             setCases([
                 { id: 1, name: "Бесплатный", image_url: "/freenonfon.png", price: 0, currency: "tickets", is_limited: false },
                 { id: 2, name: "Новогодний", image_url: "/NewYearCase.png", price: 500, currency: "stars", is_limited: true, limit_total: 1000, limit_remaining: 998 }
             ]);
          }
        }
      } else {
         if (mounted) {
             setUser({ id: 1, username: "Demo User", balance_stars: 1250, balance_tickets: 5 });
             try {
                // API_URL is global now
                const casesRes = await axios.get(`${API_URL}/api/cases/`, { timeout: 2000 });
                setCases(casesRes.data);
             } catch {
                 setCases([
                     { id: 1, name: "Бесплатный", image_url: "/freenonfon.png", price: 0, currency: "tickets", is_limited: false },
                     { id: 2, name: "Новогодний", image_url: "/NewYearCase.png", price: 500, currency: "stars", is_limited: true, limit_total: 1000, limit_remaining: 998 }
                 ]);
             }
         }
      }
      if (mounted) setLoading(false);
    };
    
    const safetyTimer = setTimeout(() => {
        if (mounted && loading) setLoading(false);
    }, 7000); // Safety timer extended

    initApp();
    return () => { mounted = false; clearTimeout(safetyTimer); };
  }, []);

  const openCase = async (caseId: number, promoCode?: string) => {
      const c = cases.find(x => x.id === caseId);
      if (!c) return;

      // Free Case Logic: Show Modal
      if (c.price === 0 && promoCode === undefined) {
          setSelectedFreeCaseId(caseId);
          setShowPromoModal(true);
          return;
      }

      if (isOpening) return;
      
      if (window.Telegram?.WebApp) window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');
      
      setOpeningCaseId(caseId);
      setIsOpening(true);
      setShowPromoModal(false);

      try {
          // API_URL is global now
          const tg = window.Telegram?.WebApp;
          
          if (c.is_limited) {
              setCases(prev => prev.map(item => item.id === caseId ? { ...item, limit_remaining: (item.limit_remaining || 0) - 1 } : item));
          }

          const res = await axios.post(`${API_URL}/api/cases/${caseId}/open`, { 
              initData: tg?.initData || "demo", 
              promo_code: promoCode || null 
          });
          
          const data = res.data;
          setTimeout(() => {
              setWonItem(data.win_item);
              setShowRewardModal(true);
              setIsOpening(false);
              setOpeningCaseId(null);
              if (data.new_balance_stars !== undefined) {
                  setUser(prev => prev ? ({ ...prev, balance_stars: data.new_balance_stars, balance_tickets: data.new_balance_tickets }) : null);
              }
          }, 2000);

      } catch (e: any) {
          setIsOpening(false);
          setOpeningCaseId(null);
          if (c.is_limited) {
               setCases(prev => prev.map(item => item.id === caseId ? { ...item, limit_remaining: (item.limit_remaining || 0) + 1 } : item));
          }
          
          let msg = "Ошибка открытия";
          if (axios.isAxiosError(e) && e.response) {
              if (e.response.status === 400 && e.response.data.detail.includes("COOLDOWN")) {
                  const seconds = e.response.data.detail.split(":")[1];
                  const hours = Math.ceil(Number(seconds)/3600);
                  msg = `Кейс доступен через ${hours}ч`;
              } else {
                  msg = e.response.data.detail;
              }
          }
          if (window.Telegram?.WebApp) window.Telegram.WebApp.showAlert(msg);
          else alert(msg);
      }
  };

  if (loading) return <Loader />;

  return (
    <main className="flex min-h-screen flex-col max-w-md mx-auto shadow-2xl text-zinc-100 font-sans relative overflow-hidden">
      
      {/* Ambient Background Effects */}
      <div className="gold-dust"></div>
      
      <div className="fixed inset-0 pointer-events-none z-0">
          <div className="absolute top-[-20%] left-[20%] w-[60%] h-[60%] bg-violet-600/20 blur-[120px] rounded-full animate-pulse-glow"></div>
          <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-600/10 blur-[100px] rounded-full animate-pulse-glow delay-1000"></div>
      </div>

      {/* Header with EXTRA EXTRA Safe Area Padding */}
      <header className="sticky top-0 z-50 bg-[#05050a]/80 backdrop-blur-xl px-4 py-3 flex justify-between items-center border-b border-white/5 shadow-lg mt-0 pt-24 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-zinc-700/50 to-zinc-900/50 p-[1px] shadow-inner">
             <div className="w-full h-full rounded-xl bg-[#0a0a0f] overflow-hidden flex items-center justify-center">
                {user?.photo_url ? (
                    <img src={user.photo_url} alt="ava" className="w-full h-full object-cover" />
                ) : (
                    <span className="font-bold text-zinc-400">{user?.username?.[0]}</span>
                )}
             </div>
          </div>
          <div className="flex flex-col">
             <div className="flex items-center gap-2">
                 <span className="font-bold text-sm text-white tracking-wide drop-shadow-md">{user?.username}</span>
                 {user?.is_admin && <span className="bg-red-600 text-white text-[8px] px-1.5 py-0.5 rounded font-bold tracking-widest shadow-[0_0_10px_rgba(220,38,38,0.5)]">ADMIN</span>}
             </div>
             <span className="text-[10px] text-emerald-500 font-mono uppercase tracking-wider flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Online
             </span>
          </div>
        </div>
        
        <div className="flex gap-2">
            <CurrencyBadge icon={Star} value={user?.balance_stars} color="text-yellow-400" />
            <CurrencyBadge icon={Hexagon} value={user?.balance_tickets} color="text-fuchsia-500" isToken />
        </div>
      </header>

      {/* CONTENT */}
      <div className="flex-1 pb-24 z-10 relative">
        {activeTab === "home" && <HomeView user={user} onOpenModal={() => setShowInfoModal(true)} subTaskStatus={subTaskStatus} onCheckSub={handleCheckSubscription} />}
        {activeTab === "cases" && <CasesView cases={cases} onOpen={openCase} />}
        {activeTab === "upgrade" && <UpgradeView />}
        {activeTab === "arena" && <ArenaView />}
        {activeTab === "profile" && <ProfileView user={user} />}
      </div>

      {/* NAV */}
      <nav className="fixed bottom-0 left-0 right-0 bg-[#05050a]/90 backdrop-blur-xl border-t border-white/5 pb-safe pt-2 px-4 flex justify-between items-center z-50 max-w-md mx-auto">
          <NavItem active={activeTab === "home"} onClick={() => setActiveTab("home")} icon={HomeIcon} label="Главная" />
          <NavItem active={activeTab === "upgrade"} onClick={() => setActiveTab("upgrade")} icon={Zap} label="Апгрейд" />
          
          <div className="relative -top-6" onClick={() => setActiveTab("cases")}>
            <div className={`w-16 h-16 rounded-full flex items-center justify-center shadow-2xl transform transition-all active:scale-95 cursor-pointer border-[5px] border-[#05050a] ${activeTab === "cases" ? "bg-gradient-to-b from-yellow-400 to-yellow-600 shadow-yellow-500/50 scale-110" : "bg-zinc-800"}`}>
                <Gift className={`w-7 h-7 ${activeTab === "cases" ? "text-zinc-900 animate-bounce" : "text-zinc-400"}`} />
            </div>
          </div>

          <NavItem active={activeTab === "arena"} onClick={() => setActiveTab("arena")} icon={Swords} label="Арена" />
          <NavItem active={activeTab === "profile"} onClick={() => setActiveTab("profile")} icon={Users} label="Профиль" />
      </nav>

      {/* PROMO MODAL */}
      {showPromoModal && (
          <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 animate-in fade-in duration-200">
              <div className="absolute inset-0 bg-black/90 backdrop-blur-sm" onClick={() => setShowPromoModal(false)}></div>
              <div className="relative bg-zinc-900 border border-white/10 rounded-2xl p-6 max-w-sm w-full shadow-2xl animate-in zoom-in-95 duration-200">
                  <button onClick={() => setShowPromoModal(false)} className="absolute top-4 right-4 text-zinc-500 hover:text-white"><X className="w-5 h-5"/></button>
                  
                  <h3 className="text-xl font-bold text-white mb-6 text-center uppercase italic tracking-wider">Бесплатный кейс</h3>
                  
                  <div className="space-y-6">
                      <div>
                          <label className="text-[10px] font-bold text-zinc-500 uppercase mb-2 block tracking-widest">Ввести Промокод</label>
                          <div className="flex gap-2">
                              <input 
                                  type="text" 
                                  value={promoCodeInput}
                                  onChange={(e) => setPromoCodeInput(e.target.value.toUpperCase())}
                                  placeholder="PROMO..." 
                                  className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white font-bold placeholder:text-zinc-700 focus:outline-none focus:border-violet-500 transition uppercase tracking-widest"
                              />
                              <button 
                                  onClick={() => selectedFreeCaseId && openCase(selectedFreeCaseId, promoCodeInput)}
                                  disabled={!promoCodeInput}
                                  className="bg-violet-600 hover:bg-violet-500 text-white px-5 rounded-xl font-bold disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg shadow-violet-900/20"
                              >
                                  <CheckIcon />
                              </button>
                          </div>
                      </div>
                      
                      <div className="flex items-center gap-4">
                          <div className="h-px bg-zinc-800 flex-1"></div>
                          <span className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">ИЛИ</span>
                          <div className="h-px bg-zinc-800 flex-1"></div>
                      </div>

                      <div>
                           <div className="bg-zinc-950/50 border border-dashed border-zinc-800 rounded-xl p-4 mb-3">
                               <div className="flex justify-between items-center mb-2">
                                   <span className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Пригласить 10 друзей</span>
                                   {/* Mock progress for now, in real app use user.referrals_count */}
                                   <span className="text-[10px] text-emerald-500 font-bold bg-emerald-900/20 px-1.5 py-0.5 rounded">0 / 10</span>
                               </div>
                               <div className="w-full bg-zinc-900 h-1.5 rounded-full overflow-hidden">
                                   <div className="bg-emerald-500 h-full w-[0%]"></div> 
                               </div>
                           </div>
                           <button 
                                onClick={() => selectedFreeCaseId && openCase(selectedFreeCaseId, "")}
                                className="w-full py-3.5 bg-zinc-800 hover:bg-zinc-700 text-white font-bold text-xs uppercase tracking-wider rounded-xl transition border border-white/5"
                           >
                               Открыть (Выполнил условия)
                           </button>
                      </div>
                  </div>
              </div>
          </div>
      )}

      {/* INFO MODAL */ // Keep existing
      }
      {showInfoModal && (
          <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center p-4 animate-in fade-in duration-200">
              <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setShowInfoModal(false)}></div>
              <div className="relative bg-zinc-900 border border-white/10 rounded-2xl p-6 max-w-sm w-full animate-in slide-in-from-bottom-10 duration-300 shadow-2xl">
                  <button onClick={() => setShowInfoModal(false)} className="absolute top-4 right-4 p-1 bg-zinc-800 rounded-full text-zinc-400 hover:text-white">
                      <X className="w-5 h-5" />
                  </button>
                  
                  <div className="flex flex-col items-center text-center">
                      <div className="w-16 h-16 bg-gradient-to-br from-violet-500 to-fuchsia-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-violet-500/30">
                          <Sparkles className="w-8 h-8 text-white" />
                      </div>
                      <h3 className="text-2xl font-black text-white mb-2 uppercase italic">Winter Legends</h3>
                      <p className="text-sm text-zinc-400 mb-6 leading-relaxed">
                          Это <strong>платный Battle Pass</strong>, который откроет доступ к премиум наградам. Прокачивай уровни и забирай топовый дроп!
                      </p>
                      
                      <div className="space-y-3 w-full mb-6">
                          <div className="bg-zinc-800/50 p-3 rounded-xl flex items-center gap-3 border border-white/5">
                              <Gift className="w-5 h-5 text-yellow-400" />
                              <span className="text-sm font-bold text-zinc-200">Множество подарков и скинов</span>
                          </div>
                          <div className="bg-zinc-800/50 p-3 rounded-xl flex items-center gap-3 border border-white/5">
                              <Star className="w-5 h-5 text-violet-400" />
                              <span className="text-sm font-bold text-zinc-200">Горы Звезд для открытий</span>
                          </div>
                          <div className="bg-zinc-800/50 p-3 rounded-xl flex items-center gap-3 border border-white/5">
                              <TicketIcon className="w-5 h-5 text-emerald-500" />
                              <span className="text-sm font-bold text-zinc-200">Промокоды от наших партнеров</span>
                          </div>
                      </div>

                      <button onClick={() => setShowInfoModal(false)} className="w-full py-3.5 bg-white text-black font-bold rounded-xl hover:bg-zinc-200 transition active:scale-95 shadow-lg shadow-white/10">
                          Понятно, жду!
                      </button>
                  </div>
              </div>
          </div>
      )}

      </main>
  );
}

// --- VIEWS ---

function HomeView({ user, onOpenModal, subTaskStatus, onCheckSub }: { user: User | null, onOpenModal: () => void, subTaskStatus: string, onCheckSub: () => void }) {
    const refCount = user?.referrals_count || 0;
    const tasks = [
        { 
            title: "Подписка на канал", 
            reward: "1 Купон", 
            icon: TicketIcon,
            isToken: true,
            done: subTaskStatus === 'done', 
            action: onCheckSub, 
            status: subTaskStatus 
        },
        { 
            title: "Пригласить 10 друзей", 
            reward: "500", 
            icon: Star,
            isToken: false,
            done: refCount >= 10,
            progress: `${Math.min(refCount, 10)}/10`,
            action: () => {}, 
            status: refCount >= 10 ? 'done' : 'go'
        },
        { 
            title: "Пригласить 20 друзей", 
            reward: "1000", 
            icon: Star,
            isToken: false,
            done: refCount >= 20,
            progress: `${Math.min(refCount, 20)}/20`,
            action: () => {}, 
            status: refCount >= 20 ? 'done' : 'go'
        },
    ];

    return (
        <div className="px-4 pt-6 space-y-8 animate-in fade-in duration-500">
            {/* Battle Pass Banner (Active & Colorful) */}
            <div className="carbon-card rounded-2xl p-0 relative overflow-hidden group cursor-pointer shadow-2xl shadow-violet-900/20 border border-violet-500/30 min-h-[200px]" onClick={onOpenModal}>
                {/* Background Image/Gradient */}
                <div className="absolute inset-0 bg-gradient-to-r from-[#0f172a] via-[#1e1b4b] to-[#2e1065]"></div>
                
                {/* Glow Effect */}
                <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_30%_50%,rgba(124,58,237,0.15),transparent_70%)]"></div>
                
                {/* Decorative Image (Right side - HERO) */}
                 <div className="absolute -right-4 -bottom-8 w-[180px] h-[180px] md:w-[220px] md:h-[220px] rotate-[-5deg] transition-transform duration-500 group-hover:scale-105 group-hover:rotate-0 z-0">
                    <Image 
                        src="/battlepass.png" 
                        alt="Battle Pass" 
                        width={250} 
                        height={250} 
                        className="object-contain drop-shadow-[0_0_30px_rgba(139,92,246,0.5)]" 
                    />
                 </div>

                {/* Content */}
                <div className="relative z-10 p-6 flex flex-col items-start h-full justify-between min-h-[200px]">
                    <div className="max-w-[60%]">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-black/40 backdrop-blur-md rounded-full mb-3 border border-white/10 shadow-lg">
                            <Sparkles className="w-3 h-3 text-yellow-400 animate-pulse" />
                            <span className="text-[10px] font-bold text-white tracking-widest uppercase text-shadow">Скоро</span>
                        </div>
                        <h2 className="text-3xl font-black text-white uppercase italic tracking-tight drop-shadow-2xl leading-[0.9] mb-2">
                            Winter<br/>
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-amber-400 to-yellow-500 drop-shadow-sm">Legends</span>
                        </h2>
                        <p className="text-xs text-violet-200 font-medium leading-tight drop-shadow-md">
                            Сезон 1: Уникальные награды и челленджи
                        </p>
                    </div>
                    
                    <button className="mt-auto px-6 py-3 bg-white text-violet-950 font-black rounded-xl text-xs shadow-[0_0_20px_rgba(255,255,255,0.3)] flex items-center gap-2 group-hover:scale-105 transition-all active:scale-95 hover:bg-zinc-100">
                        УЗНАТЬ БОЛЬШЕ <ChevronRight className="w-3 h-3" />
                    </button>
                </div>
            </div>

            {/* Contests / Tasks */}
            <div>
                 <div className="flex justify-between items-end mb-4">
                    <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Активные задания</h3>
                    <span className="text-[10px] text-emerald-400 font-mono">Обновлено сегодня</span>
                 </div>
                 
                 <div className="space-y-2">
                     {tasks.map((t, i) => (
                         <div key={i} className="carbon-card p-3 rounded-xl flex items-center justify-between border border-white/5">
                             <div className="flex items-center gap-3">
                                 <div className={`w-9 h-9 rounded-xl flex items-center justify-center shadow-inner ${t.done ? 'bg-green-500/10 text-green-500' : 'bg-zinc-800 text-zinc-400'}`}>
                                     {t.done ? <CheckIcon /> : <Trophy className="w-4 h-4" />}
                                 </div>
                                 <div>
                                     <div className="text-sm font-bold text-zinc-200">{t.title}</div>
                                     <div className="flex items-center gap-2 mt-0.5">
                                        {t.isToken ? (
                                            <span className="text-[10px] font-bold text-fuchsia-400 flex items-center gap-1">
                                                +{t.reward} <TicketIcon className="w-3 h-3 animate-pulse" />
                                            </span>
                                        ) : (
                                            <span className="text-[10px] font-bold text-yellow-400 flex items-center gap-1">
                                                +{t.reward} <Star className="w-3 h-3 fill-current" />
                                            </span>
                                        )}
                                        {/* Progress */}
                                        {t.progress && !t.done && (
                                            <span className="text-[9px] font-bold text-zinc-500 bg-zinc-900 px-1.5 py-0.5 rounded ml-1">
                                                {t.progress}
                                            </span>
                                        )}
                                     </div>
                                 </div>
                             </div>
                             <button 
                                onClick={t.action}
                                disabled={t.done || t.status !== 'check' && t.status !== 'go'} // Only clickable if check or go
                                className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase transition-all ${
                                    t.done ? 'text-green-500 bg-transparent' : 
                                    t.status === 'check' ? 'bg-blue-600 text-white animate-pulse shadow-lg shadow-blue-500/30' : 
                                    'bg-zinc-800 text-zinc-400 hover:bg-white hover:text-black'
                                }`}
                             >
                                 {t.done ? 'ГОТОВО' : t.status === 'check' ? 'ПРОВЕРИТЬ' : 'GO'}
                             </button>
                         </div>
                     ))}
                 </div>
            </div>
        </div>
    )
}

function CasesView({ cases, onOpen }: { cases: Case[], onOpen: (id: number) => void }) {
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
                        <CaseCard key={c.id} title={c.name} image={c.image_url} glow="blue" />
                    ))}
                </div>
            </div>
        </div>
    )
}

// ... (UpgradeView, ArenaView, ProfileView, and all Helper components remain EXACTLY the same as before. Copy-paste them here from previous file state)

function UpgradeView() {
    return (
        <div className="px-4 pt-6 h-full flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-300">
            <h2 className="text-xl font-bold text-center mb-8">Апгрейд</h2>
            <div className="flex-1 flex flex-col justify-center items-center gap-8">
                <div className="flex items-center gap-4 w-full justify-center">
                    <div className="w-32 h-32 carbon-card rounded-2xl flex items-center justify-center border-dashed border-zinc-700 cursor-pointer hover:border-zinc-500 transition">
                        <span className="text-zinc-600 text-4xl font-thin">+</span>
                    </div>
                    <ChevronRight className="w-6 h-6 text-zinc-600" />
                    <div className="w-32 h-32 carbon-card rounded-2xl flex items-center justify-center border-dashed border-zinc-700 cursor-pointer hover:border-zinc-500 transition relative overflow-hidden">
                        <div className="absolute inset-0 bg-violet-500/5"></div>
                        <span className="text-zinc-600 text-4xl font-thin">+</span>
                    </div>
                </div>
                <div className="flex flex-col items-center gap-2">
                    <div className="text-zinc-500 text-xs uppercase tracking-widest">Шанс успеха</div>
                    <div className="text-4xl font-bold text-white font-mono">50%</div>
                </div>
                <button className="w-full max-w-xs bg-zinc-800 text-zinc-500 font-bold py-4 rounded-xl cursor-not-allowed border border-white/5">
                    Выберите предметы
                </button>
            </div>
        </div>
    )
}

function ArenaView() {
    const battles = [
        { id: 1, case: "Golden Dragon", price: 500, player1: "Alex", player2: null },
        { id: 2, case: "Daily", price: 0, player1: "Dimon", player2: "Bot" },
    ]
    return (
        <div className="px-4 pt-6 h-full flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-300">
             <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-white flex items-center justify-center gap-2">
                    <Swords className="w-6 h-6 text-red-500" /> Арена
                </h2>
                <p className="text-sm text-zinc-400">Победитель забирает всё</p>
             </div>
             <div className="flex gap-2 mb-4">
                 <button className="flex-1 py-3 bg-red-600 hover:bg-red-500 rounded-xl font-bold text-sm text-white shadow-lg shadow-red-900/20 transition">
                     Создать битву
                 </button>
                 <button className="px-4 bg-zinc-800 rounded-xl border border-white/5">
                     <Settings className="w-5 h-5 text-zinc-400" />
                 </button>
             </div>
             <div className="space-y-3">
                 <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Активные битвы</h3>
                 {battles.map((b) => (
                     <div key={b.id} className="carbon-card p-3 rounded-xl flex items-center justify-between group cursor-pointer hover:border-red-500/30 transition">
                         <div className="flex items-center gap-3">
                             <div className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center border border-zinc-700">
                                 <span className="font-bold text-xs">{b.player1[0]}</span>
                             </div>
                             <div className="flex flex-col">
                                 <span className="text-xs font-bold text-white">{b.case}</span>
                                 <span className="text-[10px] text-zinc-500">{b.price} <span className="text-yellow-500">★</span></span>
                             </div>
                         </div>
                         <div className="w-8 h-8 rounded-full bg-zinc-950 border border-zinc-800 flex items-center justify-center z-10">
                             <span className="text-[10px] font-bold text-red-500">VS</span>
                         </div>
                         <div className="flex items-center gap-3">
                             {b.player2 ? (
                                 <div className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center border border-zinc-700 grayscale opacity-50">
                                     <span className="font-bold text-xs">{b.player2[0]}</span>
                                 </div>
                             ) : (
                                 <button className="px-4 py-2 bg-green-600/20 text-green-500 border border-green-500/30 rounded-lg text-[10px] font-bold hover:bg-green-500 hover:text-white transition">
                                     ИГРАТЬ
                                 </button>
                             )}
                         </div>
                     </div>
                 ))}
                 {[1,2,3].map(i => (
                     <div key={i + 10} className="h-16 rounded-xl border border-dashed border-zinc-800 flex items-center justify-center">
                         <span className="text-[10px] text-zinc-600">Ожидание игроков...</span>
                     </div>
                 ))}
             </div>
        </div>
    )
}

function ProfileView({ user }: { user: User | null }) {
    const [copied, setCopied] = useState(false);
    const inviteLink = `https://t.me/PrimeGiftBot?start=${user?.referral_code || "123"}`;
    const handleCopy = () => {
        navigator.clipboard.writeText(inviteLink);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
        if (window.Telegram?.WebApp) window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
    };
    const handleShare = () => {
         if (window.Telegram?.WebApp) {
             const text = "Залетай в Prime Gift! Открывай кейсы и лутай NFT. Вот тебе бонус: ";
             const url = `https://t.me/share/url?url=${inviteLink}&text=${encodeURIComponent(text)}`;
             window.Telegram.WebApp.openTelegramLink(url);
         }
    };
    return (
        <div className="px-4 pt-6 animate-in fade-in slide-in-from-bottom-4 duration-300 pb-20">
            <div className="flex flex-col items-center mb-8">
                <div className="relative">
                    <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-zinc-700 to-zinc-900 p-1 mb-3 shadow-2xl">
                        <div className="w-full h-full rounded-xl bg-zinc-900 overflow-hidden">
                            {user?.photo_url ? <img src={user.photo_url} className="w-full h-full object-cover" /> : (
                                <div className="w-full h-full flex items-center justify-center text-4xl font-bold text-zinc-700">{user?.username?.[0]}</div>
                            )}
                        </div>
                    </div>
                    <div className="absolute -bottom-1 -right-1 bg-zinc-900 p-1 rounded-lg border border-zinc-800">
                         {user?.is_admin ? (
                             <div className="bg-red-600 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow-lg shadow-red-900/50">ADMIN</div>
                         ) : (
                             <div className="bg-emerald-500/20 text-emerald-500 text-[10px] font-bold px-2 py-0.5 rounded">PRO</div>
                         )}
                    </div>
                </div>
                <h2 className="text-2xl font-bold text-white">{user?.username}</h2>
                <div className="flex items-center gap-2 mt-1">
                    <span className="text-zinc-500 text-xs bg-zinc-900 px-2 py-0.5 rounded border border-white/5 font-mono">ID: {user?.id}</span>
                </div>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-6">
                <div className="carbon-card p-4 rounded-xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-2 opacity-10">
                        <Star className="w-12 h-12 text-yellow-500" />
                    </div>
                    <div className="text-2xl font-bold text-white">{user?.balance_stars}</div>
                    <div className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider mt-1">Баланс Звезд</div>
                </div>
                <div className="carbon-card p-4 rounded-xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-2 opacity-10">
                        <Gift className="w-12 h-12 text-blue-500" />
                    </div>
                    <div className="text-2xl font-bold text-white">0</div>
                    <div className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider mt-1">Открыто кейсов</div>
                </div>
            </div>
            <div className="mb-6">
                <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <Users className="w-4 h-4" /> Реферальная программа
                </h3>
                <div className="carbon-card rounded-xl p-5 border border-violet-500/20 relative overflow-hidden">
                    <div className="absolute -top-10 -right-10 w-32 h-32 bg-violet-600/20 blur-[50px] rounded-full"></div>
                    <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-lg bg-violet-500/20 flex items-center justify-center">
                                <Hexagon className="w-6 h-6 text-violet-400 animate-pulse" />
                            </div>
                            <div>
                                <div className="font-bold text-white text-sm">Пригласи друга</div>
                                <div className="text-xs text-violet-300">+1 Токен за каждого</div>
                            </div>
                        </div>
                        <div className="bg-zinc-950/50 border border-dashed border-zinc-700 rounded-lg p-3 flex items-center justify-between mb-4">
                            <div className="flex flex-col overflow-hidden">
                                <span className="text-[10px] text-zinc-500">Твоя ссылка</span>
                                <span className="text-xs text-zinc-300 font-mono truncate w-48 opacity-70">{inviteLink}</span>
                            </div>
                            <button onClick={handleCopy} className={`p-2 rounded-md transition-all ${copied ? 'bg-green-500 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-white'}`}>
                                {copied ? <CheckIcon /> : <Copy className="w-4 h-4" />}
                            </button>
                        </div>
                        <button onClick={handleShare} className="w-full py-3 bg-violet-600 hover:bg-violet-500 text-white font-bold rounded-xl shadow-lg shadow-violet-900/30 transition flex items-center justify-center gap-2 active:scale-95">
                            Пригласить друга
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

function Loader() {
    return (
        <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-[#050505] overflow-hidden font-sans">
            {/* Falling Snow */}
            {Array.from({ length: 20 }).map((_, i) => (
                <div key={i} className="snowflake" style={{
                    left: `${Math.random() * 100}%`,
                    animationDuration: `${Math.random() * 3 + 2}s`,
                    animationDelay: `${Math.random() * 2}s`,
                    opacity: Math.random()
                }}></div>
            ))}

            {/* Background Effects */}
            <div className="absolute top-[-20%] left-[-20%] w-[70%] h-[70%] bg-violet-600/20 blur-[120px] rounded-full animate-pulse-glow"></div>
            <div className="absolute bottom-[-20%] right-[-20%] w-[70%] h-[70%] bg-blue-600/20 blur-[120px] rounded-full animate-pulse-glow" style={{ animationDelay: "1s" }}></div>

            {/* Logo Area */}
            <div className="relative flex flex-col items-center z-10">
                <div className="relative mb-8">
                    <div className="absolute inset-0 bg-violet-500 blur-[40px] opacity-50 animate-pulse"></div>
                    <Gift className="w-24 h-24 text-white relative z-10 drop-shadow-[0_0_15px_rgba(139,92,246,0.8)] animate-bounce-slow" />
                </div>
                
                <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-violet-200 to-white tracking-tighter italic uppercase mb-2 drop-shadow-lg animate-pulse">
                    Prime Gift
                </h1>
                <span className="text-xs text-yellow-400 font-bold tracking-widest uppercase mb-8 animate-pulse">Happy New Year</span>

                {/* Progress Bar */}
                <div className="w-64 h-1.5 bg-zinc-800/50 rounded-full overflow-hidden backdrop-blur-sm border border-white/10">
                    <div className="h-full bg-gradient-to-r from-violet-600 via-fuchsia-500 to-blue-600 animate-load-bar w-full origin-left"></div>
                </div>
                <div className="mt-4 text-[10px] font-bold text-zinc-500 uppercase tracking-[0.3em] animate-pulse">
                    System Loading...
                </div>
            </div>
        </div>
    )
}

function CurrencyBadge({ icon: Icon, value, color, isToken }: any) {
    return (
        <div className="flex items-center gap-1.5 bg-zinc-900/80 border border-white/5 px-3 py-1.5 rounded-full">
            <Icon className={`w-3.5 h-3.5 ${color} ${isToken ? 'animate-pulse' : ''} fill-current`} />
            <span className={`text-xs font-bold text-zinc-100`}>{value || 0}</span>
            {!isToken && <div className="w-px h-3 bg-zinc-700 mx-1"></div>}
            {!isToken && <span className="text-[10px] text-blue-500 cursor-pointer hover:text-blue-400">+</span>}
        </div>
    )
}

function NavItem({ active, onClick, icon: Icon, label }: any) {
    return (
        <button onClick={onClick} className={`flex flex-col items-center gap-1 w-14 transition-all duration-200 ${active ? 'text-white scale-105' : 'text-zinc-500 hover:text-zinc-300'}`}>
            <Icon className={`w-5 h-5 ${active ? 'fill-current' : ''}`} />
            <span className="text-[9px] font-medium">{label}</span>
        </button>
    )
}

function CheckIcon() {
    return (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
    )
}

function LimitedCaseCard({ data, onOpen }: { data: Case, onOpen: () => void }) {
    const total = data.limit_total || 1000;
    const remaining = data.limit_remaining || 0;
    const percent = (remaining / total) * 100;

    return (
        <div className="w-full rounded-3xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.01] bg-gradient-to-r shadow-purple-900/20 border-purple-500/20 from-purple-950/40 to-zinc-900 border border-white/5 h-48">
            <div className="absolute -left-10 -top-10 w-40 h-40 blur-[60px] rounded-full opacity-20 bg-purple-500"></div>
            <div className="flex h-full relative z-10 bg-zinc-950/40 backdrop-blur-sm p-0 gap-4">
                <div className="w-44 h-full flex-shrink-0 relative flex items-center justify-center -ml-4">
                     <img 
                        src={data.image_url} 
                        alt={data.name} 
                        className="w-full h-[120%] object-contain drop-shadow-2xl transition-transform group-hover:scale-105" 
                     />
                </div>
                <div className="flex flex-col justify-center flex-1 py-4 pr-5">
                    <div className="mb-2 text-right">
                        <h3 className="font-black text-2xl text-white leading-none tracking-tight uppercase italic">{data.name}</h3>
                        <div className="text-[10px] text-zinc-400 font-mono mt-1">Осталось: <span className="text-white font-bold">{remaining}</span> шт</div>
                    </div>
                    <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-4">
                        <div className="h-full bg-gradient-to-r from-fuchsia-600 to-purple-500 transition-all duration-500" style={{ width: `${percent}%` }}></div>
                    </div>
                    <button onClick={onOpen} className="w-full relative group overflow-hidden rounded-xl transition-all duration-300 hover:shadow-[0_0_25px_rgba(234,179,8,0.6)] active:scale-95">
                        <div className="absolute inset-0 bg-gradient-to-b from-amber-300 via-amber-500 to-amber-600"></div>
                        <div className="absolute inset-0 opacity-30 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]"></div>
                        <div className="absolute top-0 left-0 right-0 h-[40%] bg-gradient-to-b from-white/60 to-transparent"></div>
                        <div className="relative py-3.5 px-4 flex items-center justify-center gap-2 z-10">
                            <span className="font-black text-white text-sm tracking-widest drop-shadow-md uppercase text-shadow-sm">ОТКРЫТЬ</span>
                            <div className="w-1 h-1 rounded-full bg-white/50 mx-1"></div>
                            <div className="flex items-center gap-1">
                                <span className="font-black text-white text-sm drop-shadow-md">{data.price}</span>
                                <Star className="w-3.5 h-3.5 fill-white text-white drop-shadow-md" />
                            </div>
                        </div>
                        <div className="absolute inset-0 border border-white/40 rounded-xl pointer-events-none"></div>
                    </button>
                </div>
            </div>
        </div>
    )
}

function CaseCard({ title, subtitle, image, glow }: any) {
    const glows: any = {
        blue: "shadow-blue-900/20 border-blue-500/20 from-blue-950/40 to-zinc-900",
        purple: "shadow-purple-900/20 border-purple-500/20 from-purple-950/40 to-zinc-900"
    };
    
    const isFree = title.toLowerCase().includes("бесплатн") || title.toLowerCase().includes("ежедневн");

    return (
        <div className={`w-full h-40 rounded-3xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] bg-gradient-to-r ${glows[glow]} border`}>
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
                    <button className="w-full relative group overflow-hidden rounded-xl transition-all duration-300 hover:shadow-[0_0_20px_rgba(56,189,248,0.6)] active:scale-95">
                        <div className={`absolute inset-0 bg-gradient-to-b ${isFree ? 'from-sky-400 via-sky-500 to-blue-600' : 'from-amber-300 via-amber-500 to-amber-600'}`}></div>
                        <div className="absolute inset-0 opacity-20 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]"></div>
                        <div className="absolute top-0 left-0 right-0 h-[40%] bg-gradient-to-b from-white/50 to-transparent"></div>
                        <div className="relative py-3.5 px-4 flex items-center justify-center gap-2 z-10">
                           <Gift className="w-4 h-4 text-white drop-shadow-md animate-bounce" />
                           <span className="font-black text-white text-sm tracking-widest drop-shadow-md uppercase">
                               {isFree ? 'БЕСПЛАТНО' : 'ОТКРЫТЬ'}
                           </span>
                        </div>
                        <div className="absolute inset-0 border border-white/30 rounded-xl pointer-events-none"></div>
                    </button>
                </div>
            </div>
        </div>
    )
}
