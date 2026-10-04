// Example addresses shown on the site. Every string is copied verbatim from
// site/test/vectors.json (official public test vectors, sources listed there), and
// address.test.mjs fails if one drifts. None of them belongs to a real person's wallet
// that we know of: they come from published test data.

// The three rows of the address checker demo (#checker), in this order.
export const CHECKER_EXAMPLES = [
  {
    id: "u1",
    // zcash-test-vectors unified_address.json, index 6: Sapling + Orchard receivers,
    // no transparent receiver, the same mix as Zodl's shielded address (FACTS F27).
    addr: "u1ay3aawlldjrmxqnjf5medr5ma6p3acnet464ht8lmwplq5cd3ugytcmlf96rrmtgwldc75x94qn4n8pgen36y8tywlq6yjk7lkf3fa8wzjrav8z2xpxqnrnmjxh8tmz6jhfh425t7f3vy6p4pd3zmqayq49efl2c4xydc0gszg660q9p",
  },
  {
    id: "t1",
    // ZIP 320 reference implementation example.
    addr: "t1VmmGiyjVNeCjxDZzg7vZmd99WyzVby9yC",
  },
  {
    id: "tex1",
    // The same key as the t1 above, in its TEX form (ZIP 320 example).
    addr: "tex1s2rt77ggv6q989lr49rkgzmh5slsksa9khdgte",
  },
];

// Address detective: six rounds, answer is "shielded" or "transparent".
export const DETECTIVE = [
  { addr: "u1tqhg04ppjt6vlf2uvkygt07sqzgpclxdpn7j7ydkcr0e8ym68wn592z7uqudktrwn4u3q57flp8hw3d0wd9t0rm0e6m8eys27evfawh6zhha6eulzj86uz89swu7gtk0vcknd3dauhc96twhx20xxsp93dxahqlt7z5p04ldgy2y2lp0", answer: "shielded" },
  { addr: "t1LZdE42PAt1wREUv1YMYRFwJDPHPW8toLL", answer: "transparent" },
  { addr: "zs1qqqqqqqqqqqqqqqqqqcguyvaw2vjk4sdyeg0lc970u659lvhqq7t0np6hlup5lusxle75c8v35z", answer: "shielded" },
  { addr: "tex1yvvrncc9czsza45pgph67g39shmxywgyvsypwn", answer: "transparent" },
  { addr: "t3VDyGHn9mbyCf448m2cHTu5uXvsJpKHbiZ", answer: "transparent" },
  { addr: "u1ddnjsdcpm36r6aq79n3s68shjweksnmwtdltrh046s8m6xcws9ygyawalxx8n6hg6vegk0wh8zjnafxgh6msppjsljvyt0ynece3lvm0", answer: "shielded" },
];
