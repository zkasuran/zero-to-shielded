// The one source of episode data. Pages, menus, cards and players all read this file.
//
// To publish an episode:
//   1. put zts-eN.mp4, zts-eN.jpg (poster) and zts-eN.srt (captions) in site/media/
//   2. run `node tools/build.mjs` from site/ (it records which media files exist)
//   3. optional: set youtubeId to the YouTube video id; the player then embeds
//      youtube-nocookie.com instead of the mp4
//   4. replace the draft chapter times with the real ones and set chaptersDraft: false
//
// Chapter `t` is seconds from the start. Titles use the bounty words on purpose.

export const STEPS = [
  { id: "wallet", label: "Wallet setup", episode: "e1" },
  { id: "zec", label: "Getting ZEC", episode: "e2" },
  { id: "shield", label: "Shielding", episode: "e3" },
  { id: "unshield", label: "Unshielding", episode: "e3" },
  { id: "send", label: "Sending", episode: "e4" },
  { id: "receive", label: "Receiving", episode: "e4" },
];

export const EPISODES = [
  {
    id: "e0",
    number: 0,
    title: "Zero to Shielded in 5 videos",
    short: "The whole path",
    slug: "trailer",
    length: "0:30",
    summary: "The whole path in 30 seconds. Five short videos take you from no wallet to your first private payment.",
    outcome: "You know the path and what you need.",
    steps: [],
    youtubeId: null,
    mp4: "/media/zts-e0.mp4",
    poster: "/media/zts-e0.jpg",
    srt: "/media/zts-e0.srt",
    chaptersDraft: true,
    chapters: [
      { t: 0, title: "The path" },
      { t: 10, title: "What you need" },
      { t: 20, title: "Start with episode 1" },
    ],
  },
  {
    id: "e1",
    number: 1,
    title: "Wallet setup: install Zodl and back up your phrase",
    short: "Wallet setup",
    slug: "wallet-setup",
    length: "1:45",
    summary: "Install Zodl, a Zcash wallet for your phone. Older guides call it Zashi. Then write your recovery phrase on paper. Your recovery phrase is 24 words in a set order that bring your wallet back if you lose your phone.",
    outcome: "You have a wallet and your recovery phrase is on paper.",
    steps: ["wallet"],
    youtubeId: null,
    mp4: "/media/zts-e1.mp4",
    poster: "/media/zts-e1.jpg",
    srt: "/media/zts-e1.srt",
    chaptersDraft: true,
    chapters: [
      { t: 0, title: "What you will do" },
      { t: 12, title: "Wallet setup: install Zodl" },
      { t: 35, title: "Wallet setup: create your wallet" },
      { t: 55, title: "Wallet setup: back up your recovery phrase" },
      { t: 92, title: "Next step" },
    ],
  },
  {
    id: "e2",
    number: 2,
    title: "Getting ZEC: swap in the app or buy on an exchange",
    short: "Getting ZEC",
    slug: "getting-zec",
    length: "1:50",
    summary: "Get your first ZEC. You can swap other crypto into shielded ZEC (hidden on the blockchain) right inside Zodl. Or buy ZEC on an exchange. Most exchanges only send ZEC to a transparent address (public, like Bitcoin). That is fine. Zodl will offer to shield it when it arrives.",
    outcome: "ZEC is arriving in your wallet.",
    steps: ["zec"],
    youtubeId: null,
    mp4: "/media/zts-e2.mp4",
    poster: "/media/zts-e2.jpg",
    srt: "/media/zts-e2.srt",
    chaptersDraft: true,
    chapters: [
      { t: 0, title: "What you will do" },
      { t: 12, title: "Getting ZEC: swap in Zodl" },
      { t: 45, title: "Getting ZEC: buy on an exchange" },
      { t: 80, title: "Getting ZEC: your ZEC arrives" },
      { t: 98, title: "Next step" },
    ],
  },
  {
    id: "e3",
    number: 3,
    title: "Shielding and unshielding",
    short: "Shielding and unshielding",
    slug: "shielding-unshielding",
    length: "1:55",
    summary: "Shielding moves your own ZEC from transparent (public) to shielded (hidden). When ZEC arrives at your transparent address, Zodl shows Unshielded Balance. Tap Shield. You also learn when you need to unshield and what becomes public when you do.",
    outcome: "Your ZEC is shielded and you know when to unshield.",
    steps: ["shield", "unshield"],
    youtubeId: null,
    mp4: "/media/zts-e3.mp4",
    poster: "/media/zts-e3.jpg",
    srt: "/media/zts-e3.srt",
    chaptersDraft: true,
    chapters: [
      { t: 0, title: "What you will do" },
      { t: 12, title: "What the blockchain sees" },
      { t: 30, title: "Shielding: tap Shield" },
      { t: 60, title: "Unshielding: when you need it" },
      { t: 90, title: "If Zodl asks about Ironwood" },
      { t: 103, title: "Next step" },
    ],
  },
  {
    id: "e4",
    number: 4,
    title: "Sending and receiving: your first shielded transaction",
    short: "Sending and receiving",
    slug: "sending-receiving",
    length: "2:00",
    summary: "Share your shielded address. Shielded means the amount, sender and receiver are encrypted on the blockchain. Then send your first shielded payment with a note, a private message. Only you and the person you pay can read it. Zodl shows the fee before anything is sent.",
    outcome: "You sent and received a shielded payment with a private note.",
    steps: ["send", "receive"],
    youtubeId: null,
    mp4: "/media/zts-e4.mp4",
    poster: "/media/zts-e4.jpg",
    srt: "/media/zts-e4.srt",
    chaptersDraft: true,
    chapters: [
      { t: 0, title: "What you will do" },
      { t: 12, title: "Receiving: share your shielded address" },
      { t: 35, title: "Sending: your first shielded transaction" },
      { t: 70, title: "Receiving: the payment and note arrive" },
      { t: 95, title: "What the blockchain sees" },
      { t: 108, title: "You're shielded" },
    ],
  },
  {
    id: "e5",
    number: 5,
    title: "Stay private: five habits",
    short: "Stay private",
    slug: "stay-private",
    length: "1:15",
    summary: "Five habits keep your payments private. Keep your ZEC shielded (hidden on the blockchain). Do not shield an amount and then send the same amount to a transparent (public) address soon after. Turn on Tor. Guard your recovery phrase, the 24 words that restore your wallet. Check every address before you send.",
    outcome: "You know the habits that keep your payments private.",
    steps: [],
    youtubeId: null,
    mp4: "/media/zts-e5.mp4",
    poster: "/media/zts-e5.jpg",
    srt: "/media/zts-e5.srt",
    chaptersDraft: true,
    chapters: [
      { t: 0, title: "Five habits" },
      { t: 10, title: "Keep your ZEC shielded" },
      { t: 24, title: "Avoid matching amounts" },
      { t: 36, title: "Turn on Tor" },
      { t: 48, title: "Guard your recovery phrase" },
      { t: 60, title: "Check the address" },
    ],
  },
];

export function episodeById(id) {
  return EPISODES.find((e) => e.id === id) || null;
}

export function nextEpisode(id) {
  const i = EPISODES.findIndex((e) => e.id === id);
  return i >= 0 && i < EPISODES.length - 1 ? EPISODES[i + 1] : null;
}

export function formatTime(seconds) {
  const s = Math.max(0, Math.floor(Number(seconds) || 0));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = String(s % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${r}` : `${m}:${r}`;
}
