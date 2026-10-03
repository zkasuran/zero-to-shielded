# Narration manifest

One row per cue. To read the narration by hand instead of through the API, save each
clip as mp3 at exactly the path in the first column, then rebuild the sound only:

```bash
VOICE_ENGINE=fish MUSIC=~/Downloads/joyinsound-no-copyright-music-398375.mp3 \
  AUDIO_ONLY=1 python3 build.py projects/<project>.json
```

The build reads the real duration of each file and lays the video out around it, so
clips do not need to match any target length. Paths carry a digest of the engine, the
voice, the rate and the words, which is why this file is generated: run
`python3 manifest.py projects/*.json` after any narration edit.

Across every project here: 331 cues, 42444 characters.

## bitnet

11 cues, 1439 characters.

| file | line |
| --- | --- |
| `artifacts/bitnet/cue-00-00-fish-e4bf8c6740.mp3` | bitNET is a Bittensor subnet that watches the live TLS certificate and DNS state of the internet. |
| `artifacts/bitnet/cue-01-00-fish-7a87ec9ec7.mp3` | Certificates now rotate toward 47 day lifetimes, so a silent expiry or a botched renewal is a constant risk. |
| `artifacts/bitnet/cue-01-01-fish-3012f06fe9.mp3` | And a geo targeted hijack is invisible to any single vantage scanner. Catching it needs many independent vantages that disagree. |
| `artifacts/bitnet/cue-02-00-fish-65955ec3ff.mp3` | Each epoch a miner measures a host from its own vantage and reports the certificate fingerprint. A validator recomputes that fingerprint from one cheap handshake. |
| `artifacts/bitnet/cue-02-01-fish-bf7f7061a3.mp3` | The score is honeypot accuracy plus real target accuracy, gated by coverage. The honeypots the validator controls are the incontestable core. |
| `artifacts/bitnet/cue-03-00-fish-729497090c.mp3` | The whole stack is tested. Thirty seven tests cover the transport, the DNS and TLS measurement, the honeypot rotation and the scoring. |
| `artifacts/bitnet/cue-04-00-fish-ef099a9f24.mp3` | An adversary simulation scores honest and cheating miners with the real reward function over many epochs. |
| `artifacts/bitnet/cue-04-01-fish-7a5d226b8d.mp3` | Honest earns sixty three percent of emission, more than three times the next strategy. The fabricator and the lazy miner earn nothing. |
| `artifacts/bitnet/cue-05-00-fish-e2eaf0c369.mp3` | The score is a pure deterministic function, so two honest validators that saw the same evidence produce the same weights. Yuma consensus then clips a copier instead of honest disagreement. |
| `artifacts/bitnet/cue-06-00-fish-0cb46c4f4e.mp3` | And it is live. bitNET is deployed on the Bittensor testnet as netuid 550, with a validator and miners registered on chain. |
| `artifacts/bitnet/cue-07-00-fish-9ef0bc94a6.mp3` | Objective, cheap to verify and hard to game. That is bitNET, a decentralized oracle for the live state of the internet. |

## call-on-behalf

17 cues, 1871 characters.

| file | line |
| --- | --- |
| `artifacts/call-on-behalf/cue-00-00-fish-c4294336f5.mp3` | Some things can only be arranged by phone. A clinic with no online booking, a garage, a landlord, an office whose web form has been down for two years. |
| `artifacts/call-on-behalf/cue-01-00-fish-d8396c5e39.mp3` | If you are deaf or hard of hearing, or your language does not match the line you have to call, that is not an inconvenience. It is a door that does not open. |
| `artifacts/call-on-behalf/cue-02-00-fish-00e3da5715.mp3` | You write down what the caller may say about you. Here that is three details, and the list is a budget. |
| `artifacts/call-on-behalf/cue-02-01-fish-cb6bfd1567.mp3` | Anything not on the list does not get said. The app checks that before it dials and again against what was actually said. |
| `artifacts/call-on-behalf/cue-03-00-fish-af1f1ad563.mp3` | This is the report the errand writes. What was agreed, with the reference number they read out. |
| `artifacts/call-on-behalf/cue-03-01-fish-89e76bfcd7.mp3` | Then your questions, each with the answer in their own words. |
| `artifacts/call-on-behalf/cue-03-02-fish-a26a4b4fde.mp3` | Insurance, and what to bring on the day. Answered, not guessed. |
| `artifacts/call-on-behalf/cue-03-03-fish-f1fceb547f.mp3` | And a privacy check at the bottom. Nothing outside your list was said. |
| `artifacts/call-on-behalf/cue-04-00-fish-15965ba138.mp3` | The transcript is part of the deliverable, not a debug log. The call opens by saying it is automated and who it is calling for. |
| `artifacts/call-on-behalf/cue-04-01-fish-c156cdb678.mp3` | They ask for a date of birth. That was on the list, so the caller gives it and nothing more. |
| `artifacts/call-on-behalf/cue-05-00-fish-af857da831.mp3` | Three gates guard that budget. First the request file: a question with a national identifier buried in it, refused when the file loads. |
| `artifacts/call-on-behalf/cue-05-01-fish-d3216bf84f.mp3` | Then the script it would read out. An email address nobody authorized, so it stops before dialling. Calls placed, zero. |
| `artifacts/call-on-behalf/cue-05-02-fish-2e800e3d62.mp3` | The third gate runs on what was actually said, and it reports the finding back, masked, to the person it belongs to. |
| `artifacts/call-on-behalf/cue-06-00-fish-779147f2d8.mp3` | Plenty of businesses will not deal with an automated caller. That is a real answer, so it is recorded as the outcome and you are told to call another way. |
| `artifacts/call-on-behalf/cue-06-01-fish-09041e9d10.mp3` | It does not argue and it does not dial back. |
| `artifacts/call-on-behalf/cue-07-00-fish-dba4a93375.mp3` | It is not a relay service. A relay service carries a live conversation, and this does not. It runs one errand from a script you approved, and it never claims to be you. |
| `artifacts/call-on-behalf/cue-07-01-fish-37f7c937fd.mp3` | The pull request is open, and the whole thing runs against a local fake first, with no account. |

## cartograph

8 cues, 1089 characters.

| file | line |
| --- | --- |
| `artifacts/cartograph/cue-00-00-fish-9d193b90d6.mp3` | Enterprise search is hard not because extraction is hard but because the same person has three names, sources disagree and half the questions have no answer at all. We turn the corpus into an ontology in HydraDB and answer by walking it. |
| `artifacts/cartograph/cue-01-00-fish-613a70e33c.mp3` | Five hundred and thirty employees, thirty products and nearly five thousand artifacts, loaded as a typed graph. |
| `artifacts/cartograph/cue-01-01-fish-07bd22e8b8.mp3` | Ask who wrote and reviewed a report and the answer is a walk from the artifact to its people, returning exact ids. |
| `artifacts/cartograph/cue-02-00-fish-11e16f598a.mp3` | Every structural question is a typed edge traversal: authored, reviewed, participated, on team. |
| `artifacts/cartograph/cue-02-01-fish-e93262307e.mp3` | Ten different employees are named Charlie Brown and the graph keeps them apart by role, org and neighbourhood. |
| `artifacts/cartograph/cue-03-00-fish-a5165091cd.mp3` | On the structural query types the graph is exact and it declines the seven hundred unanswerable questions by reachability. |
| `artifacts/cartograph/cue-03-01-fish-7d0f2ea358.mp3` | Off the shelf graph RAG scores about ten on this benchmark, so answering exactly and abstaining honestly is a real step. |
| `artifacts/cartograph/cue-04-00-fish-a3a9a79d90.mp3` | Structural questions become graph traversals and the unanswerable ones are declined by reachability. The free text half is left to a reader on purpose. The ontology is the product. |

## coolroute

16 cues, 2253 characters.

| file | line |
| --- | --- |
| `artifacts/coolroute/cue-00-00-fish-2dc3f03690.mp3` | A city forecast gives one number for a whole city. It cannot tell an outdoor worker which street bakes hardest at two in the afternoon or that the early morning start is far cooler in how it feels. |
| `artifacts/coolroute/cue-01-00-fish-f112c4d424.mp3` | Shade, surface and humidity move the felt temperature by more than the map does. Cool Route Planner is an agent that calls the FortyGuard Temperature API as its tools and answers with a decision rather than a number. |
| `artifacts/coolroute/cue-02-00-fish-286c47dc0a.mp3` | Ask for the coolest walking route. The agent scores each path on felt temperature and shade, then picks the park detour over the exposed arterial. |
| `artifacts/coolroute/cue-02-01-fish-4cf5c3eadd.mp3` | Ask for the coolest two hour window and it names the seven o'clock start. Every reading is labelled mock, because the FortyGuard key is issued only after registration. |
| `artifacts/coolroute/cue-03-00-fish-f4468b2ce3.mp3` | This is the captured proof that it is a real agent. Given a heat question the model buys the find coolest hour tool, then grounds its answer in the numbers the tool returned. |
| `artifacts/coolroute/cue-03-01-fish-d3c1fb0ba7.mp3` | Given a question that needs no data it answers free, with no tool call. The numbers come from the API, never from the language model. |
| `artifacts/coolroute/cue-03-02-fish-5f74ad315a.mp3` | Both cases pass. |
| `artifacts/coolroute/cue-04-00-fish-2eb376487d.mp3` | This is the tool the agent bought a moment ago. Find coolest hour, described for the model in plain language. |
| `artifacts/coolroute/cue-04-01-fish-7cc3bc107b.mp3` | It takes a location, a date and candidate start hours. The model fills these in and the planner runs the ranking against the API. |
| `artifacts/coolroute/cue-05-00-fish-4cf689d356.mp3` | The live path is the documented contract. Every call posts with the key in the api key header. |
| `artifacts/coolroute/cue-05-01-fish-b32171a1db.mp3` | A submission returns an activity id, then the client polls status until the reading is ready. Swapping this in for the mock is one line of config. |
| `artifacts/coolroute/cue-06-00-fish-5a4673bc56.mp3` | Thirty five tests, all offline, all green. They cover the heat model, the planners, the agent loop with a scripted model and the live request contract with a mocked transport. |
| `artifacts/coolroute/cue-07-00-fish-5d85148b74.mp3` | Here is the same planner on the deployed page. One click ranks the routes and another ranks the time windows. |
| `artifacts/coolroute/cue-07-01-fish-6ccc0fb016.mp3` | The page shows which backend answered, so a viewer always knows whether a reading is live or mock. |
| `artifacts/coolroute/cue-08-00-fish-84926c914e.mp3` | And the same command on the live backend places a real call to the FortyGuard API and ranks real readings. Nothing above the adapter changed. |
| `artifacts/coolroute/cue-09-00-fish-82a6ab7f4e.mp3` | Cool Route Planner treats heat as a routing cost and a scheduling constraint. Every number is grounded in the API, the mock is labelled everywhere it appears and the live path is one line of config away. |

## devwell

10 cues, 1258 characters.

| file | line |
| --- | --- |
| `artifacts/devwell/cue-00-00-fish-e82ba7ce96.mp3` | Developers forget to drink, move and rest. DevWell fixes that from inside Kiro. It ships as a Kiro plugin: an MCP server, agent hooks and a wellness coach, all spec-driven. No separate terminal. |
| `artifacts/devwell/cue-01-00-fish-61002571cb.mp3` | This is the live site. DevWell drops into Kiro over MCP and runs from inside your session, fully local with no cloud. |
| `artifacts/devwell/cue-01-01-fish-acc1584228.mp3` | Thirty four MCP tools, four health domains, a hundred and forty four tests and every byte stays on your machine. |
| `artifacts/devwell/cue-02-00-fish-109c54a8dc.mp3` | Because this is a Kiro hackathon, Kiro is the home. Agent hooks make DevWell proactive. One greets each session as your health companion. |
| `artifacts/devwell/cue-02-01-fish-c6d939bb3c.mp3` | Another fires on every tool use and injects a nudge. No background daemon, it runs on real Kiro events. |
| `artifacts/devwell/cue-03-00-fish-5c6aa22a7f.mp3` | Here is what that hook injects when water is overdue. A short, caring line right in your Kiro session, not a wall of text. |
| `artifacts/devwell/cue-04-00-fish-030720c8e2.mp3` | None of this was vibe coded. Every domain started as a Kiro spec with numbered requirements. |
| `artifacts/devwell/cue-04-01-fish-be21b660a2.mp3` | Hydration, movement, nutrition and mindfulness, each specified before it was built. |
| `artifacts/devwell/cue-05-00-fish-7979d0f094.mp3` | And it is proven. A hundred and forty four tests across nine files, all green, including the plugin and the regression tests. |
| `artifacts/devwell/cue-06-00-fish-ab004ee94d.mp3` | DevWell. A spec-driven Kiro plugin that lives in your session, tracks your health for real and coaches you in your flow. Built with Kiro for the Ready, Spec, Ship Hackathon. |

## edgewright

9 cues, 1471 characters.

| file | line |
| --- | --- |
| `artifacts/edgewright/cue-00-00-fish-393a0a0b23.mp3` | Edgewright is a live console for the redirect and rewrite rules that route your site. It works across eleven hosting platforms. Its whole point is that a person and an AI agent can work the same rules together, over WebMCP. |
| `artifacts/edgewright/cue-01-00-fish-b53444658e.mp3` | This is the product. Your redirect rules, live in the browser. It opens on a real bug, a broad shop rule sitting above the specific sale rule. |
| `artifacts/edgewright/cue-01-01-fish-022fbc9a50.mp3` | First match wins, so the specific rule below the broad one never runs and the sale link 404s in production. A person or an agent can fix it right here. |
| `artifacts/edgewright/cue-02-00-fish-3b045090ef.mp3` | Ask the agent to fix it and it uses the tools. test_url finds the 404. audit_rules names the shadowed rule. reorder_rule lifts the specific one up, then it re-tests. |
| `artifacts/edgewright/cue-02-01-fish-923058cb32.mp3` | Every tool call shows on the page with its real output. That is the experience: not a chatbot in a side panel, but an agent operating the console you are looking at. |
| `artifacts/edgewright/cue-03-00-fish-ca41fe98ac.mp3` | Each tool is real WebMCP. A name, a typed input schema, a read-only hint the agent trusts to run it without asking. |
| `artifacts/edgewright/cue-03-01-fish-b1f4b04806.mp3` | The typed schema is why the agent calls the tool precisely instead of guessing at the UI. The tools that change rules drop the hint, so the agent confirms first. |
| `artifacts/edgewright/cue-04-00-fish-07cfd801be.mp3` | The same engine powers a second app. Studio migrates your whole config to another host, then replays every URL through both and proves they resolve identically. Move platforms without breaking a link. |
| `artifacts/edgewright/cue-05-00-fish-8fd9661086.mp3` | One engine, three apps, fifteen WebMCP tools, eleven platforms, 148 tests. Edgewright is the web working with agents, built for the WebMCP Challenge. |

## harmonicut

9 cues, 1472 characters.

| file | line |
| --- | --- |
| `artifacts/harmonicut/cue-00-00-fish-6c475bbfed.mp3` | A marimba bar, struck, rings at inharmonic overtones near one, two point seven six and five point four. It sounds clangy. Makers fix it by carving an undercut into the underside. Finding that undercut is an inverse-design problem. harmonicut solves it with gradients. |
| `artifacts/harmonicut/cue-01-00-fish-c6c47aba39.mp3` | Why is this a Tesseract problem? The forward physics is a generalized eigensolve, which automatic differentiation cannot reach through. |
| `artifacts/harmonicut/cue-01-01-fish-698180111e.mp3` | So the geometry side is analytic autodiff and the solver side is finite differences. Tesseract composes across that boundary, which is what makes it load-bearing. |
| `artifacts/harmonicut/cue-02-00-fish-929861432f.mp3` | Here it runs. The end-to-end gradient from jax dot grad matches a global finite-difference check to about one part in a thousand. |
| `artifacts/harmonicut/cue-02-01-fish-4f682c2db7.mp3` | That proves the gradient really crosses the autodiff to finite-difference boundary. Then gradient descent tunes the partials from two point eight and five point six toward four and ten. |
| `artifacts/harmonicut/cue-03-00-fish-1147ff7edb.mp3` | This is the entire composition. apply_tesseract wraps each container as a JAX function. The geometry feeds the eigensolver and the loss closes the loop. |
| `artifacts/harmonicut/cue-04-00-fish-087483729b.mp3` | The result page carries the same check and the tuned bar. The partials end near three point eight and nine point one, close to the marimba ideal. |
| `artifacts/harmonicut/cue-04-01-fish-2ce3bf7d2e.mp3` | The undercut the optimiser carves is the shape real makers cut by hand, an independent sign the gradients point the right way. |
| `artifacts/harmonicut/cue-05-00-fish-8756edf508.mp3` | harmonicut. Two Tesseracts composed across a real boundary, one end-to-end gradient, a bar tuned toward harmonic. Built with Tesseract for the twenty twenty-six hackathon. |

## kane-loop

14 cues, 1472 characters.

| file | line |
| --- | --- |
| `artifacts/kane-loop/cue-00-00-fish-19c689fda9.mp3` | AI agents write code fast. The part that never closed is trust. When the agent ships something, a human still opens a browser and clicks through to see if it actually works. |
| `artifacts/kane-loop/cue-01-00-fish-ef361675f8.mp3` | kane-loop closes that loop. You save a file and it notices. |
| `artifacts/kane-loop/cue-01-01-fish-167c8becf5.mp3` | It runs your Kane flow in a real browser. When the total is wrong, Kane fails the run. |
| `artifacts/kane-loop/cue-01-02-fish-258b6df056.mp3` | The failure and the value Kane saw go to your coding agent, which edits the code. |
| `artifacts/kane-loop/cue-01-03-fish-df5d4e53c7.mp3` | The save re-fires Kane and it passes. No human touched the browser. |
| `artifacts/kane-loop/cue-02-00-fish-4e7ea6b328.mp3` | Here is that loop on a real run. The discount math is broken, so on the first pass Kane fails it in a real browser. |
| `artifacts/kane-loop/cue-02-01-fish-d2435af8dc.mp3` | The agent reads the failure and patches the source. |
| `artifacts/kane-loop/cue-02-02-fish-e261fdb76d.mp3` | The next save re-runs Kane and it is green. Nobody touched the browser. |
| `artifacts/kane-loop/cue-03-00-fish-59b3fddd3d.mp3` | This is the code the agent fixed. The promo discount comes off the subtotal before tax, so two units with the twenty five percent code total sixty six dollars. |
| `artifacts/kane-loop/cue-04-00-fish-2acbc51f61.mp3` | kane-loop uses the whole Kane surface, not one command. The live run in agent mode. |
| `artifacts/kane-loop/cue-04-01-fish-056edd020d.mp3` | Committable test files that replay from cache for free, plus a product spec turned into acceptance criteria. |
| `artifacts/kane-loop/cue-04-02-fish-53b7503b7c.mp3` | Many tests sealed into one evidence pack, the evidence the agent fixes from, live credits and a Playwright export. |
| `artifacts/kane-loop/cue-05-00-fish-6759d4f4bb.mp3` | And here is the checkout itself, deployed and live. Set a quantity, apply a promo, watch the order total update. This is the app the loop just verified. |
| `artifacts/kane-loop/cue-06-00-fish-9b4fe34342.mp3` | kane-loop is the loop that closes the gap. Real Kane runs, a real self-heal, the whole suite, all on a live URL. Built for the Kane CLI Online Hackathon. |

## kudzu

8 cues, 1131 characters.

| file | line |
| --- | --- |
| `artifacts/kudzu/cue-00-00-fish-ba9a69e4ae.mp3` | When a dependency is compromised, the question is not whether the package is bad. It is which of your own services can actually reach it, through which chain and how deep. For a whole fleet against a whole incident, that is a graph traversal. |
| `artifacts/kudzu/cue-01-00-fish-a0fe7d93a9.mp3` | Twenty real npm tools as a fleet, their real dependency trees and a hundred and seventeen real advisories from OSV over forty seven releases. Nine of the twenty are exposed. |
| `artifacts/kudzu/cue-01-01-fish-27c43b8f7f.mp3` | Each exposed service comes with its exact chain to the compromise, resolved by bounded reachability inside HydraDB. |
| `artifacts/kudzu/cue-02-00-fish-0f0c507c48.mp3` | The verdict is a bounded variable length reachability query to the compromised releases, so it is complete and not a truncated walk. |
| `artifacts/kudzu/cue-02-01-fish-998af1444c.mp3` | Reverse blast radius uses a path procedure with the direction flipped, which a plain match cannot express. |
| `artifacts/kudzu/cue-03-00-fish-a572c71909.mp3` | The finding is published and reproducible, every number from real deps.dev and OSV data. |
| `artifacts/kudzu/cue-03-01-fish-fc93245aa8.mp3` | The chokepoints are the packages the most services depend on, the ones to pin first. |
| `artifacts/kudzu/cue-04-00-fish-9e6a7cc825.mp3` | Many compromised packages against a whole fleet, resolved in one path-procedure call. A graph problem a vector database cannot touch. The exact chains and the chokepoints are all in the repo. |

## moonwalk-grant

37 cues, 4880 characters.

| file | line |
| --- | --- |
| `artifacts/moonwalk-grant/cue-00-00-fish-4cefa422f2.mp3` | This is MoonWalk's codebase walkthrough for the Circle grant. Four Circle products, the file each one lives in, then the run that proves it works. |
| `artifacts/moonwalk-grant/cue-00-01-fish-5e21dcee47.mp3` | Everything here is Arc testnet. No real funds move. There are no users and no revenue, and every figure on screen is a demo measurement. |
| `artifacts/moonwalk-grant/cue-01-00-fish-4e0b9e5487.mp3` | Start with what is running. The MoonWalk service answers on Arc testnet with a USDC payment channel open on chain. |
| `artifacts/moonwalk-grant/cue-01-01-fish-07235877ba.mp3` | Half a dollar deposited, twelve thousand atomic units redeemed, the rest outstanding. Guarded means the spend cap contract sits in the path. |
| `artifacts/moonwalk-grant/cue-01-02-fish-3681508fdc.mp3` | Source reads chain, so the price the agent is quoted comes from a registry contract rather than a database. |
| `artifacts/moonwalk-grant/cue-02-00-fish-302b3ddb74.mp3` | The chain is Arc testnet, and the three MoonWalk contracts answer with real bytecode on it. |
| `artifacts/moonwalk-grant/cue-02-01-fish-f1ce6da19d.mp3` | Circle's USDC is a predeploy on Arc, and it is the unit every payment in this video is denominated in. |
| `artifacts/moonwalk-grant/cue-03-00-fish-71e8332975.mp3` | Circle product one, developer controlled Wallets. Every rail in MoonWalk asks a wallet for exactly one thing, an EIP seven one two signature. |
| `artifacts/moonwalk-grant/cue-03-01-fish-7b76910dc6.mp3` | An address, and a way to sign typed data. Nothing else, so the rest of the app never learns where the key lives. |
| `artifacts/moonwalk-grant/cue-04-00-fish-f5350e7cb4.mp3` | Here is the Circle implementation. MoonWalk hands the payload to Circle's sign typed data endpoint, and Circle signs it with the wallet's key inside its own custody. |
| `artifacts/moonwalk-grant/cue-04-01-fish-2892871735.mp3` | A fresh entity secret ciphertext per request, because Circle requires one, then sixty five bytes back. Anything else is an error rather than a shrug. |
| `artifacts/moonwalk-grant/cue-05-00-fish-1c196d576a.mp3` | This is Circle answering about the wallet it holds for us. Blockchain arc testnet, custody type developer, state live. |
| `artifacts/moonwalk-grant/cue-05-01-fish-6faaf3e07c.mp3` | And the line that matters. This wallet has never sent a transaction, because it never needs to. It signs. |
| `artifacts/moonwalk-grant/cue-06-00-fish-2e27c536bc.mp3` | This is the strongest single check in the integration. MoonWalk builds the EIP seven one two digest of a channel voucher locally. |
| `artifacts/moonwalk-grant/cue-06-01-fish-301bc8b843.mp3` | Then it asks the NanoChannel contract on Arc for its own voucher hash and compares the two byte for byte. They agree. |
| `artifacts/moonwalk-grant/cue-06-02-fish-7b8a7eb271.mp3` | Circle signs that digest, and the signature recovers to the wallet address Circle named. Custody, our encoder and the contract all agree before anything settles. |
| `artifacts/moonwalk-grant/cue-07-00-fish-33890f53bc.mp3` | Circle product two, USDC. The same Circle custodied wallet signs an EIP three oh oh nine transfer authorization. |
| `artifacts/moonwalk-grant/cue-07-01-fish-49189f58b4.mp3` | Arc USDC checks that signature under eth call and accepts it. A relayer would submit it, so the wallet moves USDC without paying gas. Nothing was broadcast here. |
| `artifacts/moonwalk-grant/cue-08-00-fish-02e631970b.mp3` | The service side of the channel. Before any work happens it recovers the voucher signature and refuses anything not signed by the channel payer. |
| `artifacts/moonwalk-grant/cue-08-01-fish-7b694baecc.mp3` | Then the cumulative must be exactly what the ledger expects, and the remaining cap comes from the SpendGuard contract. A refusal and a failed settlement cannot disagree. |
| `artifacts/moonwalk-grant/cue-09-00-fish-a61fc5c670.mp3` | And this is the batch. Nothing settles until the accrued total crosses a threshold, or the caller forces it. |
| `artifacts/moonwalk-grant/cue-09-01-fish-9e6b9f72c8.mp3` | Then every outstanding voucher goes into a single redeem call, whatever the number of calls behind it. |
| `artifacts/moonwalk-grant/cue-10-00-fish-9792ae7274.mp3` | Circle product three, CCTP version two. When the agent's own Arc balance drops under a threshold it has to refill itself. |
| `artifacts/moonwalk-grant/cue-10-01-fish-00f06f08db.mp3` | Every input to that decision is a field on one frozen plan. Needed is false when the balance is already fine, and then the honest answer is to do nothing. |
| `artifacts/moonwalk-grant/cue-11-00-fish-0678d0476f.mp3` | The fee comes from Circle's Iris service, per finality level, and a missing level fails loudly. A max fee under Iris's minimum means the burn is never attested. |
| `artifacts/moonwalk-grant/cue-12-00-fish-08ff327621.mp3` | The refill script in its default dry run mode. It asks both chains whether the route is real, reads Circle's live fee and builds the calldata. |
| `artifacts/moonwalk-grant/cue-12-01-fish-9dac59143f.mp3` | Then it asks the contract whether the burn would succeed. Eth call says it would, and no key was loaded and nothing was signed. |
| `artifacts/moonwalk-grant/cue-13-00-fish-5560c3be65.mp3` | Circle product four, Gateway, and this one carries a caveat that stays on screen. MoonWalk reads Gateway. It does not write to it. |
| `artifacts/moonwalk-grant/cue-13-01-fish-476d0040db.mp3` | It is the closest first party thing to our own channel, so the docs compare against Circle's real numbers. Half a payment rail would be worse than none. |
| `artifacts/moonwalk-grant/cue-14-00-fish-6dbd98802d.mp3` | Both Gateway views answered live, Circle's balances API on Arc domain twenty six and the Gateway wallet contract. Zero balance, because we have never deposited. |
| `artifacts/moonwalk-grant/cue-15-00-fish-cbd00cced8.mp3` | Now the number the whole design exists for. One x four oh two settlement of a single tenth of a cent call burned eighty seven thousand one hundred and forty five gas. |
| `artifacts/moonwalk-grant/cue-15-01-fish-72f7b5d1f1.mp3` | Thirty metered calls settled in one transfer for two hundred and sixty two thousand six hundred and thirty nine gas. That is eight thousand seven hundred and fifty five a call. |
| `artifacts/moonwalk-grant/cue-15-02-fish-582d7986dd.mp3` | Eight and a half times cheaper at thirty calls. Break even is about four. A demo measurement on testnet, not usage. |
| `artifacts/moonwalk-grant/cue-16-00-fish-27ac80a956.mp3` | The repository's own gates, run just now. One hundred and ninety nine Python tests, and mypy strict clean over thirty two modules. |
| `artifacts/moonwalk-grant/cue-16-01-fish-67de017cea.mp3` | Ruff clean, formatting clean and fifty one Foundry tests on the contracts. |
| `artifacts/moonwalk-grant/cue-17-00-fish-8e28388865.mp3` | Four Circle products, and for each one the file where it is implemented. Wallets, USDC, CCTP with Iris and Gateway read only. |
| `artifacts/moonwalk-grant/cue-17-01-fish-e032f59304.mp3` | Arc testnet, no real funds and no users yet. The code and the receipts are public, so every number here can be checked. |

## moonwalk

17 cues, 2046 characters.

| file | line |
| --- | --- |
| `artifacts/moonwalk/cue-00-00-fish-f68e77266d.mp3` | An agent that pays per call hits a wall. On Arc, settling a tenth of a cent costs nearly two tenths of a cent in gas, so the meter moves into a database where the receipt is a row somebody can edit. |
| `artifacts/moonwalk/cue-01-00-fish-6ef61398cd.mp3` | MoonWalk puts the meter in a contract. This is the channel, open on Arc right now, read straight off the chain. |
| `artifacts/moonwalk/cue-01-01-fish-c211d3d4e1.mp3` | A deposit funded by one signature, the amount settled so far, then the word guarded, which matters next. |
| `artifacts/moonwalk/cue-02-00-fish-b903f605cf.mp3` | One full run against those contracts, out of the receipt the script wrote as it went. |
| `artifacts/moonwalk/cue-02-01-fish-c503c074af.mp3` | The payer funds once, then signs one voucher a call. Thirty calls settle in a single transfer, about two hundredths of a cent each, against nearly two tenths alone. |
| `artifacts/moonwalk/cue-02-02-fish-5644879e17.mp3` | Then the part that needed a contract. Bob's voucher goes over his cap, so the chain refuses it. Not our backend. Nobody can redeem it later, us included. |
| `artifacts/moonwalk/cue-02-03-fish-a98b6b9e4a.mp3` | The payer sent nothing all run. Zero transactions before, zero after. |
| `artifacts/moonwalk/cue-03-00-fish-2a14f7d4cf.mp3` | That refusal lives in the source, in the guard contract. |
| `artifacts/moonwalk/cue-03-01-fish-fac452a7fe.mp3` | A total over the limit reverts with CapExceeded. The service asks this contract before it does the work, so a refusal and a failed settlement can never disagree. |
| `artifacts/moonwalk/cue-04-00-fish-5dfa1cb3bd.mp3` | The batch is a contract too. The newest voucher per person, each checked against the payer's signature. A replay or a stale total reverts. |
| `artifacts/moonwalk/cue-04-01-fish-027668485b.mp3` | Then the whole batch pays the service in one transfer. That single transfer is why thirty calls cost a fifth of a cent each. |
| `artifacts/moonwalk/cue-05-00-fish-6e335c0328.mp3` | All three contracts are deployed and live on Arc, on the project's own page. |
| `artifacts/moonwalk/cue-05-01-fish-7fbe131d85.mp3` | Every address links to the explorer. The repo is public, so a judge can clone it and re-derive every number. |
| `artifacts/moonwalk/cue-06-00-fish-26339afc5e.mp3` | Circle's own rails are in the code too. The agent refills its Arc balance with CCTP, asking both chains whether the route is real first. |
| `artifacts/moonwalk/cue-06-01-fish-a1eb785e73.mp3` | The dry run is the default. It reads Circle's live fee, builds the calldata, asks the contract whether it would succeed, then signs nothing. |
| `artifacts/moonwalk/cue-07-00-fish-5f975abff2.mp3` | One wallet for the room, a limit per person held in a contract, thirty sub cent calls in one transaction. |
| `artifacts/moonwalk/cue-07-01-fish-1d61c53097.mp3` | Fifty one contract tests. A hundred and ninety nine Python tests. Every figure here came out of a file the code wrote. |

## multi-party-scheduler

14 cues, 1766 characters.

| file | line |
| --- | --- |
| `artifacts/multi-party-scheduler/cue-00-00-fish-7c0e985256.mp3` | A leaking pipe needs three people in one room. A tenant, a plumber and the building superintendent. None of them share a calendar, and two of them only answer the phone. |
| `artifacts/multi-party-scheduler/cue-01-00-fish-f318d08e7f.mp3` | So somebody sits with a phone and works down the list. The failure is always the same. Two people said yes, the third could not make it, and the first two were never told. |
| `artifacts/multi-party-scheduler/cue-02-00-fish-bf04b5d259.mp3` | It calls them one at a time, and it uses what it just heard. The plumber can do two of the three. |
| `artifacts/multi-party-scheduler/cue-02-01-fish-f5e7c6f451.mp3` | So the tenant is asked about two options, not three, and one of those is gone straight away. |
| `artifacts/multi-party-scheduler/cue-02-02-fish-3b88f24ac1.mp3` | The superintendent hears a single option. The pale cells are calls nobody had to make, and one column survives all three. |
| `artifacts/multi-party-scheduler/cue-03-00-fish-c532c2c6c7.mp3` | Booked with all three. Six calls placed, two saved against the worst case. |
| `artifacts/multi-party-scheduler/cue-03-01-fish-ec497bdf72.mp3` | That grid is drawn from this ledger file, written while the run happened, not from a summary afterwards. |
| `artifacts/multi-party-scheduler/cue-04-00-fish-5ec54e399a.mp3` | Same three people, and now no time works. The plumber can only do the first option. |
| `artifacts/multi-party-scheduler/cue-04-01-fish-b3c0604d22.mp3` | The tenant rules that one out, which empties the set, so the superintendent is never called at all. Two calls answer a question that usually costs six. |
| `artifacts/multi-party-scheduler/cue-05-00-fish-37862c2e06.mp3` | Third run. Two people have already said yes, and the last one pulls out on the confirm call. |
| `artifacts/multi-party-scheduler/cue-05-01-fish-5530358090.mp3` | Nothing is booked, so it calls the two who committed and releases them, most recent first. That is the call a human coordinator forgets at five on a Friday. |
| `artifacts/multi-party-scheduler/cue-06-00-fish-c49c70d07f.mp3` | Replay reads the ledger back and recomputes the feasible set, the chosen time and the outcome from the recorded answers. |
| `artifacts/multi-party-scheduler/cue-06-01-fish-507eae0f01.mp3` | Widen one recorded answer to keep a time the tenant ruled out, and replay refuses it. The booking has to follow from the answers, not from the log saying so. |
| `artifacts/multi-party-scheduler/cue-07-00-fish-280255d79a.mp3` | Plan first, which places no calls and needs no credentials. Then one live run. Fifty seven tests, the pull request is open, and twenty free calls is enough to try the whole thing. |

## overhear

8 cues, 1305 characters.

| file | line |
| --- | --- |
| `artifacts/overhear/cue-00-00-fish-0465883dcb.mp3` | There is always more worth understanding than there is time to sit and read. Overhear turns any topic, or a whole article, into something you can just listen to. |
| `artifacts/overhear/cue-01-00-fish-8988242318.mp3` | You type a topic, or paste an article, and pick how you want to hear it. |
| `artifacts/overhear/cue-01-01-fish-df48e14292.mp3` | A curious explainer, a two-sided debate, a cozy wind-down, or a hype trailer. Then you press generate. |
| `artifacts/overhear/cue-02-00-fish-a685e2c8c4.mp3` | MiniMax M3 reasons out the episode: a title, an outline, and a two-host script where one host asks and an expert answers. MiniMax Speech 2.8 voices every line, two distinct voices, with a different emotion per line, so a surprised question does not sound like a calm one. MiniMax Music 3.0 writes an original theme from lyrics the model wrote about your topic. |
| `artifacts/overhear/cue-03-00-fish-05144e4288.mp3` | The key never leaves the server. Music takes about a minute to render, longer than a serverless function may run, so this route streams from the edge and keeps the connection alive until the theme is ready. |
| `artifacts/overhear/cue-03-01-fish-af9485ac7f.mp3` | Then your browser mixes the voices and a ducked music bed into one file you can play, download and share. |
| `artifacts/overhear/cue-04-00-fish-59ca1950f2.mp3` | It is real and it is tested. The unit suite covers the reasoning output and the audio timeline, and a headless browser runs the whole pipeline against the live site. |
| `artifacts/overhear/cue-05-00-fish-982652125a.mp3` | Everything you heard was generated live from one prompt. Reasoning, speech and music, all MiniMax, all on GMI Cloud. That is Overhear. |

## palimpsest

8 cues, 1006 characters.

| file | line |
| --- | --- |
| `artifacts/palimpsest/cue-00-00-fish-f135da48b8.mp3` | Cross session memory is where long context models fall down. They lose updates, they lose the order of events and they will not say when the answer is simply not there. So we do not store and retrieve. We model memory as a graph and walk it. |
| `artifacts/palimpsest/cue-01-00-fish-3241293d0f.mp3` | On a thirty question LongMemEval slice that holds back thirty percent for abstention, overall accuracy is point eight three. |
| `artifacts/palimpsest/cue-01-01-fish-2238d78b83.mp3` | Abstention is point eight nine. Temporal reasoning and assistant recall are perfect. |
| `artifacts/palimpsest/cue-02-00-fish-7d3acbd920.mp3` | Retrieval is a bounded reachability query from the question's entities to the facts they can reach. |
| `artifacts/palimpsest/cue-02-01-fish-3d8dd5801d.mp3` | Multi hop questions are answered by the path connecting two entities, found with a graph procedure. |
| `artifacts/palimpsest/cue-03-00-fish-e85481ed61.mp3` | When nothing is reachable, the honest answer is that it is not in the history instead of a nearest neighbour guess. |
| `artifacts/palimpsest/cue-03-01-fish-7847ca1d2a.mp3` | A newer fact supersedes an older one, so a knowledge update returns the current value. |
| `artifacts/palimpsest/cue-04-00-fish-2f4b74ecde.mp3` | The graph handles exactly what long context models drop. It is honest when it does not know. Every mechanic is proven against a live HydraDB node in the repo. |

## phone-approval-gate

16 cues, 1852 characters.

| file | line |
| --- | --- |
| `artifacts/phone-approval-gate/cue-00-00-fish-188e367156.mp3` | A pipeline is about to deploy to production. It stops, and it calls a person. |
| `artifacts/phone-approval-gate/cue-01-00-fish-86dd9925b6.mp3` | This is the part every team handles badly. The change needs one sign-off, the owner is asleep or in a car, and it is two in the morning. |
| `artifacts/phone-approval-gate/cue-01-01-fish-ad953c29b9.mp3` | So the change waits for hours, or somebody taps approve on a phone screen without reading it. |
| `artifacts/phone-approval-gate/cue-02-00-fish-98cdf28371.mp3` | It goes into a pipeline as one step. The action lives in the repository, so a workflow pulls it by path. |
| `artifacts/phone-approval-gate/cue-02-01-fish-2ea2b5d39c.mp3` | You hand it the request file and a key. If nobody approves, this step fails, so every step after it is skipped. |
| `artifacts/phone-approval-gate/cue-03-00-fish-eaaaf4b276.mp3` | Preview prints the exact words the call will say. It contacts nothing. |
| `artifacts/phone-approval-gate/cue-03-01-fish-4b1b373da7.mp3` | To approve, the person has to read back a six digit code printed on the request. The caller never says that code, so an approval proves whoever answered could see the change they were approving. |
| `artifacts/phone-approval-gate/cue-04-00-fish-a1ae450722.mp3` | Here is that step inside a run. Checks, then tests, then the phone call. |
| `artifacts/phone-approval-gate/cue-04-01-fish-a7018ebefe.mp3` | The release owner picks up and answers the way the call asks, so the gate exits zero. |
| `artifacts/phone-approval-gate/cue-04-02-fish-81e40a56e1.mp3` | Deploy runs. That is the only route that reaches it. |
| `artifacts/phone-approval-gate/cue-05-00-fish-16340e0324.mp3` | Same pipeline, same request, one difference. Somebody answers, sounds willing, and cannot produce the code. |
| `artifacts/phone-approval-gate/cue-05-01-fish-c0211e3d21.mp3` | Exit twenty. The deploy step is skipped. A yes on its own does not ship anything, and that is the whole app. |
| `artifacts/phone-approval-gate/cue-06-00-fish-cb4f0459e6.mp3` | Every run leaves a hash chained record that carries the inputs the outcome was computed from. |
| `artifacts/phone-approval-gate/cue-06-01-fish-be432fdd40.mp3` | So take that file, rewrite one verdict from not approved to approved, recompute its hash, and verification still rejects it. The verdict has to follow from the evidence. |
| `artifacts/phone-approval-gate/cue-07-00-fish-9889537e96.mp3` | It is honest about what it proves. Answering an enrolled handset is possession, not identity, and NIST calls the phone network a restricted channel for this. So it is an authorization control with an evidence trail. |
| `artifacts/phone-approval-gate/cue-07-01-fish-a81783e5b1.mp3` | One input switches it to dual control, two people on two handsets. The pull request is open, seventy three tests, and the whole thing runs against a local fake first. |

## ridgeline

9 cues, 1478 characters.

| file | line |
| --- | --- |
| `artifacts/ridgeline/cue-00-00-fish-57c25add9a.mp3` | The maintainers say the next gains may come from better labels, not bigger models. So how good are the labels we already have? Dataset059 is a released training set of surface patches. Its labels were drawn without ever reading the CT, which is exactly what makes this a fair question to ask. |
| `artifacts/ridgeline/cue-01-00-fish-e6c81ca95e.mp3` | Forty patches, a fixed random sample across three scrolls. On every one, the label sits a median of two point three voxels off the CT sheet ridge. |
| `artifacts/ridgeline/cue-01-01-fish-160640dab8.mp3` | We move the label onto the ridge, then score the move with meijering, a ridge filter the snap never used. It lands higher on all forty. |
| `artifacts/ridgeline/cue-01-02-fish-e0e34e45a7.mp3` | And with raw CT intensity, which has no ridge machinery at all, so the gain cannot be an artifact of one filter. Forty out of forty again. |
| `artifacts/ridgeline/cue-02-00-fish-e9ce3fad11.mp3` | This is why the result holds. The scorer refuses to grade the move with the signal the snap chased. |
| `artifacts/ridgeline/cue-02-01-fish-d32e9ed8d8.mp3` | It also refuses frangi, the operator the labels were built from. Score with either and the code raises, so the finding can never be circular by accident. |
| `artifacts/ridgeline/cue-03-00-fish-87198a9ca8.mp3` | The finding is published and reproducible. Two scripts pull the sample and rerun the audit from scratch. |
| `artifacts/ridgeline/cue-03-01-fish-f94e7c7a87.mp3` | A prior published attempt at snapping surfaces on this data reported a negative. Scored honestly on an independent witness, the drift is real and it is correctable. |
| `artifacts/ridgeline/cue-04-00-fish-41954e840b.mp3` | A producer-agnostic audit, calibrated on synthetic phantoms with a known answer, then run on the real released set. Forty of forty patches, on two independent witnesses. The labels can be moved onto the ridge. The tool that does it is in the repo. |

## sanad

18 cues, 2392 characters.

| file | line |
| --- | --- |
| `artifacts/sanad/cue-00-00-fish-c5e7db8176.mp3` | The Central Bank of the UAE requires a purpose of payment code on every outbound transfer. Banks carry it in the first line of a free text field, because the message has nowhere better to put it. |
| `artifacts/sanad/cue-01-00-fish-d6ae1c78a9.mp3` | A stablecoin transfer does not even have the free text field. So every rail keeps the instruction in a private database, and the audit trail becomes a row somebody can edit. |
| `artifacts/sanad/cue-01-01-fish-cc4f77cc60.mp3` | Sanad puts the instruction on the chain, in the same transaction as the money. |
| `artifacts/sanad/cue-02-00-fish-f0ca0954b1.mp3` | This is the deployed product, at zkasuran dot github dot io slash sanad. Four numbers, each one read from the same snapshot the audit tab reads. |
| `artifacts/sanad/cue-02-01-fish-038e88f0ef.mp3` | A sixth of a cent per payee with the instruction included, eight payments settled, and every run's authorization recomputed from the chain and matched. |
| `artifacts/sanad/cue-03-00-fish-10bd2414dc.mp3` | A Dubai trading company paying four counterparties abroad. One run, and every line carries both codes. |
| `artifacts/sanad/cue-03-01-fish-c1a870fc6e.mp3` | Every payee is screened against Arc's own denylist, which is a contract on the chain rather than a vendor subscription. |
| `artifacts/sanad/cue-03-02-fish-8eb995cf29.mp3` | The mandate and all four payouts go out as one transaction, simulated before anything is signed. |
| `artifacts/sanad/cue-04-00-fish-0e8037cd57.mp3` | Arc ships two contracts that look like they cannot be combined. Both are documented as callable only by a wallet, never by another contract. |
| `artifacts/sanad/cue-04-01-fish-ae59c2a92d.mp3` | Nest them and the wallet survives both hops. So a batch where every payment carries its own instruction becomes possible, and that transaction is on Arc now. |
| `artifacts/sanad/cue-05-00-fish-d37069cd8a.mp3` | A treasury will not put its signing key in an application, so the payer here is a Circle developer controlled wallet and this software never holds its key. |
| `artifacts/sanad/cue-05-01-fish-34331ba2ea.mp3` | That wallet has never broadcast a transaction in its life. Its money moved anyway, and both transfers still name it as the payer. |
| `artifacts/sanad/cue-06-00-fish-48ab7f4b6a.mp3` | Now delete the operator's database. There is not one. |
| `artifacts/sanad/cue-06-01-fish-ec1fede62b.mp3` | This runs with no key at all, because an audit is a read. Three log queries, then one transaction read per run. |
| `artifacts/sanad/cue-06-02-fish-899bf6085f.mp3` | Every run comes back. The payer, every payee, both purpose codes and every invoice reference, straight off the chain. |
| `artifacts/sanad/cue-07-00-fish-e25af428a0.mp3` | The same rebuild inside the product. Three runs, eight payments, every authorization recomputed from chain data and matched. |
| `artifacts/sanad/cue-07-01-fish-e2a8a6e4a2.mp3` | And the view a UAE regulator asks for, grouped by the code the Central Bank mandates, derived from the chain rather than stored anywhere. |
| `artifacts/sanad/cue-08-00-fish-2dde299059.mp3` | Sanad settles a payout run on Arc with the payment instruction attached to every line, for about a sixth of a cent per payee, and the whole audit trail rebuilds from the chain because it was never anywhere else. |

## skill-lift

15 cues, 2505 characters.

| file | line |
| --- | --- |
| `artifacts/skill-lift/cue-00-00-fish-e3d0387c39.mp3` | A skill is a folder of advice an agent can open in the middle of a task. This entry ships seven of them for a private bench mix it never sees, and its claim is that the effect was measured rather than asserted. |
| `artifacts/skill-lift/cue-01-00-fish-feea23372b.mp3` | Seven skills, sixty four kilobytes of body text between them, every description well inside the listing budget the agent pays for on every single task. |
| `artifacts/skill-lift/cue-01-01-fish-44886f44e1.mp3` | Fifty seven hard checks pass. The five review findings are printed rather than hidden, and every one of them is an office document namespace string inside a helper script. |
| `artifacts/skill-lift/cue-02-00-fish-e71937c9f5.mp3` | Under native discovery an agent opens one skill, so cross cutting discipline cannot sit in a separate skill and hope to co fire. It lives in the ground rules block that all seven carry. |
| `artifacts/skill-lift/cue-02-01-fish-5148bd25f1.mp3` | The load bearing line is the last one. Before you say the work is done, open the file you wrote, read it back from disk, then check it against the task text. |
| `artifacts/skill-lift/cue-03-00-fish-4b000d875c.mp3` | That design rests on a measurement. Thirty six probe cells, nine task shapes across four driver models, and each cell holds whichever skill the agent actually opened. |
| `artifacts/skill-lift/cue-03-01-fish-51615eb4b3.mp3` | The negative control stays clean on all four models. Nothing opens on a prompt that needs nothing, which is what makes the rest of the column worth reading. |
| `artifacts/skill-lift/cue-03-02-fish-71b1125684.mp3` | Two cells out of thirty six opened more than one skill. One skill per task is the ceiling, so every skill has to be self sufficient. |
| `artifacts/skill-lift/cue-04-00-fish-48ca9f40a4.mp3` | Fifty paired cells. Same task, same runner, one arm with the library and one without. |
| `artifacts/skill-lift/cue-04-01-fish-79c256ac3e.mp3` | Two rollouts are dropped before pairing because their with skill arm opened five skills this entry does not ship. The instrument refuses to credit us for those. |
| `artifacts/skill-lift/cue-04-02-fish-43914aa5b8.mp3` | Mean reward rises by three points. The ninety five percent interval includes zero, and it got wider as we added pairs, not narrower. That is the honest headline. |
| `artifacts/skill-lift/cue-05-00-fish-54cceed2d8.mp3` | Split the pairs by whether the with skill arm opened any skill file at all. Forty six audited pairs, eight up, four down, thirty four ties. |
| `artifacts/skill-lift/cue-05-01-fish-f62c725321.mp3` | The four unaudited pairs average exactly zero, and they hold both of the largest swings. A run that never read the library cannot credit it or blame it. |
| `artifacts/skill-lift/cue-06-00-fish-5e1b2284cd.mp3` | The audit repo is assembled from an explicit allowlist, scanned for credentials, then grepped for anything that would read as unfair practice in a winner's repository. The single accepted hit is acknowledged in the source with its reason, and the build prints it out loud. |
| `artifacts/skill-lift/cue-07-00-fish-bfd641e541.mp3` | Seven commands regenerate every number here from a clean checkout. The interval that includes zero stays in the writeup, because an entry whose whole pitch is measurement does not get to round its own result. |

## testrazor

13 cues, 1667 characters.

| file | line |
| --- | --- |
| `artifacts/testrazor/cue-00-00-fish-1276057648.mp3` | CI has two everyday failures that have nothing to do with your code. It reruns the whole suite for a one line change. A flaky test then fails at random and blocks work that is correct. testrazor fixes both, from artifacts your suite already emits. |
| `artifacts/testrazor/cue-01-00-fish-70bb5c3de4.mp3` | Impact is a dependency graph problem, not a coverage problem. Coverage is aggregated across a whole run, so it cannot say which test touched which line. |
| `artifacts/testrazor/cue-01-01-fish-21f0a02303.mp3` | So testrazor selects only the test files that reach a changed file through the import graph. A change to a config file fails safe and runs everything. |
| `artifacts/testrazor/cue-02-00-fish-6b675c0fc2.mp3` | Here it is on a sample repo. Change discount dot t s and testrazor runs only the two test files that reach it. |
| `artifacts/testrazor/cue-02-01-fish-f11c1dd314.mp3` | Change a shared dependency instead and all three run. The selection is exact, not a guess. |
| `artifacts/testrazor/cue-03-00-fish-ed42b59fa3.mp3` | Now flake. Across two runs, one test both passed and failed, so it is flaky and gets quarantined. |
| `artifacts/testrazor/cue-03-01-fish-09f6b31b25.mp3` | The gate on that same run passes, because the only failure is the quarantined flake. |
| `artifacts/testrazor/cue-03-02-fish-a14fb99da7.mp3` | Drop the quarantine and the same run fails. A real failure is never masked. That is the whole point. |
| `artifacts/testrazor/cue-04-00-fish-5f2b456070.mp3` | None of this was vibe coded. testrazor was built with Kiro's spec driven workflow, so every behaviour is a numbered acceptance criterion. |
| `artifacts/testrazor/cue-04-01-fish-33e4c6fb45.mp3` | A test that only ever fails is a consistent failure, never flaky, so a real bug is never quarantined. Every test is tagged to the criterion it covers. |
| `artifacts/testrazor/cue-05-00-fish-96a5647c09.mp3` | This is Kiro itself. In the Kiro CLI we point it at the spec and ask it to verify every acceptance criterion has a test. |
| `artifacts/testrazor/cue-05-01-fish-501c421109.mp3` | It reads the spec and every test file, then reports the matrix. Requirements one through five are fully covered. |
| `artifacts/testrazor/cue-06-00-fish-73e26ecbe2.mp3` | testrazor. Change aware, flake aware, deterministic and zero key. Built with Kiro for the Ready, Spec, Ship Hackathon. |

## tinylang

13 cues, 1855 characters.

| file | line |
| --- | --- |
| `artifacts/tinylang/cue-00-00-fish-91f8863633.mp3` | Most hackathon projects are one feature. TinyLang is a whole language toolchain. A lexer, a parser, an interpreter, a bytecode compiler, a virtual machine and a WebAssembly target, all built with Kiro's spec driven workflow. Here it is, running for real. |
| `artifacts/tinylang/cue-01-00-fish-7b04944762.mp3` | This is the live site, deployed on GitHub Pages. No server, no keys, no sign in. A judge opens this URL and the whole project is there. |
| `artifacts/tinylang/cue-01-01-fish-5cf0ef56c9.mp3` | A thousand and three tests, seventeen command line tools, three execution backends. Every number on this page is checked against the code. |
| `artifacts/tinylang/cue-02-00-fish-bc394fbeec.mp3` | Start with the interpreter. Run a Fibonacci program and it just works, recursive and iterative, up to fib of forty. |
| `artifacts/tinylang/cue-03-00-fish-f59cb10701.mp3` | Now compile the same file to bytecode. Three hundred and fifty six instructions in a six kilobyte binary. |
| `artifacts/tinylang/cue-04-00-fish-15b295d548.mp3` | Run that binary on the virtual machine and the output is identical to the interpreter, character for character. That agreement is not a hope, it is enforced by a test suite. |
| `artifacts/tinylang/cue-05-00-fish-d5c7d267a7.mp3` | There is a third backend. Compile to WebAssembly and it emits the recursive function as real wat. |
| `artifacts/tinylang/cue-05-01-fish-faa3323f1a.mp3` | And it is honest. The functions it cannot compile yet, it names and leaves out, rather than pretending. Nothing here is simulated. |
| `artifacts/tinylang/cue-06-00-fish-c239039662.mp3` | None of this was vibe coded. Every command you just saw was written first as a Kiro spec, with numbered acceptance criteria. |
| `artifacts/tinylang/cue-06-01-fish-a9e1e6c645.mp3` | Compile to bytecode, handle every language feature, report errors with a source location. The spec came first, the code followed. |
| `artifacts/tinylang/cue-07-00-fish-feea843fbd.mp3` | And the proof. The whole suite is a thousand and three tests across twenty one files, all green, nothing skipped. |
| `artifacts/tinylang/cue-07-01-fish-19c06023fd.mp3` | A hundred and ninety one of them are differential. They run each program through the interpreter and the VM and assert the output matches, with zero exclusions. That is what makes the byte identical claim real. |
| `artifacts/tinylang/cue-08-00-fish-feab08a3a3.mp3` | TinyLang. An interpreter, a bytecode VM and WebAssembly, all cross-checked, all built with Kiro for the Ready, Spec, Ship Hackathon. |

## twinrail

16 cues, 1900 characters.

| file | line |
| --- | --- |
| `artifacts/twinrail/cue-00-00-fish-465ccb1608.mp3` | A merchant wants twelve dollars fifty. The customer holds XRP, some of it on the XRP Ledger and some as FXRP on Flare. One invoice takes either, at the same price, with no bridge and no custody. |
| `artifacts/twinrail/cue-01-00-fish-e0c9f3fe62.mp3` | One command forks Coston2, so every Flare contract here is the real one. Nothing needs a faucet. |
| `artifacts/twinrail/cue-01-01-fish-2d6185a2ea.mp3` | Four addresses, all resolved by name from the contract registry. That registry is the only address the contract hardcodes. |
| `artifacts/twinrail/cue-01-02-fish-239385c6cd.mp3` | And FXRP comes out of the real asset manager at six decimals, which the contract checks rather than assumes. |
| `artifacts/twinrail/cue-02-00-fish-2b066ea406.mp3` | The merchant is owed dollars and the customer pays XRP, so something has to convert. FTSOv2 does that onchain. |
| `artifacts/twinrail/cue-02-01-fish-39f0dbd2ab.mp3` | Twelve fifty is eleven point six XRP at that reading, rounded up, so a rounding remainder never lands on the merchant. |
| `artifacts/twinrail/cue-03-00-fish-0f880b0955.mp3` | The merchant registers its own XRP Ledger address, and the contract keeps the hash the Data Connector puts in a payment proof. |
| `artifacts/twinrail/cue-03-01-fish-6e24da0446.mp3` | The quote is locked in at creation, so both rails now owe that same number of drops. |
| `artifacts/twinrail/cue-04-00-fish-37e74fc190.mp3` | The Flare rail. A drop is a millionth of an XRP and FXRP carries six decimals, so the quote transfers one for one. |
| `artifacts/twinrail/cue-04-01-fish-a5fbc83d29.mp3` | It goes payer to merchant in one transfer, and the checkout ends up holding nothing, because it never takes custody. |
| `artifacts/twinrail/cue-05-00-fish-8e4ce9a608.mp3` | A review of the first version found three real holes. This was the worst. Closing an unpaid invoice is permissionless, and an attestation round takes minutes. |
| `artifacts/twinrail/cue-05-01-fish-4eca5ad396.mp3` | So a customer who paid with a second to spare could have their invoice buried while the proof was still in flight. |
| `artifacts/twinrail/cue-06-00-fish-70b9eb44de.mp3` | The other rail settles on a Data Connector proof. So here is one built by hand, right in every single field. |
| `artifacts/twinrail/cue-06-01-fish-38b6b8ddc0.mp3` | The live verifier refuses it, because nobody ever voted on it. The invoice stays open. That is the check the whole rail rests on. |
| `artifacts/twinrail/cue-07-00-fish-8f7a4cca02.mp3` | And the run says what it does not prove. A fork cannot make a valid proof, because real providers have to vote on one. |
| `artifacts/twinrail/cue-08-00-fish-891a7e4aff.mp3` | Forty four unit tests, four more against live Coston2, and a no show is provable too. |

## verify-contact-claim

25 cues, 2242 characters.

| file | line |
| --- | --- |
| `artifacts/verify-contact-claim/cue-00-00-fish-3ada096dd1.mp3` | A voicemail says it was your bank. It leaves a number to ring back. |
| `artifacts/verify-contact-claim/cue-01-00-fish-2acdd279f9.mp3` | Every regulator says the same thing. Use the number printed on your own card, never the one in the message. |
| `artifacts/verify-contact-claim/cue-02-00-fish-cf4a035e1e.mp3` | You write down what arrived: who it claimed to be, when it came, what it asked for. |
| `artifacts/verify-contact-claim/cue-02-01-fish-04d5155869.mp3` | The number that made contact stays in the file. It is printed here, never dialled. |
| `artifacts/verify-contact-claim/cue-02-02-fish-480a139ff8.mp3` | One question, about a contact event rather than a standing fact. Did anyone there contact this person in the last hour. |
| `artifacts/verify-contact-claim/cue-03-00-fish-dfbaac6b06.mp3` | The first sentence says who the call is for. It is not a person. |
| `artifacts/verify-contact-claim/cue-03-01-fish-8657c5a8b1.mp3` | It never claims to be the customer. |
| `artifacts/verify-contact-claim/cue-04-00-fish-b942236b5a.mp3` | Six calls run against a local fake CALL-E on loopback. No key, no phone line, nothing rings. |
| `artifacts/verify-contact-claim/cue-04-01-fish-6ba1a6b2ae.mp3` | The verdict comes with the words the person on the line actually said. The transcript decides, not CALL-E's extraction. |
| `artifacts/verify-contact-claim/cue-05-00-fish-5948df17cf.mp3` | Here is a bank refusing to discuss another person's account. |
| `artifacts/verify-contact-claim/cue-05-01-fish-0ae7ec07ae.mp3` | Under Regulation P the bare fact that somebody is a customer is protected, so this is the law working rather than stonewalling. |
| `artifacts/verify-contact-claim/cue-05-02-fish-5a5e560100.mp3` | A refusal is still an answer. Nothing was verified, so the number to ring is the one on the card. |
| `artifacts/verify-contact-claim/cue-06-00-fish-42c866b813.mp3` | This next one is the product in a line. The number that made contact is never dialled. |
| `artifacts/verify-contact-claim/cue-06-01-fish-2d8d6677a3.mp3` | Point it at the number from the message and it refuses. Checking that number would be calling itself. |
| `artifacts/verify-contact-claim/cue-06-02-fish-833ca335fa.mp3` | It is checked twice. Once when the file loads, once on the words about to be sent. |
| `artifacts/verify-contact-claim/cue-07-00-fish-477cdb7eed.mp3` | Nothing the caller asked for is repeated. A card number in the file stops the run. It names the field, never the value. |
| `artifacts/verify-contact-claim/cue-07-01-fish-a821a9b884.mp3` | An instruction to impersonate the customer is refused at load as well. |
| `artifacts/verify-contact-claim/cue-08-00-fish-c33716059c.mp3` | The demo ends on counts rather than a tick. Five outcomes out of five. |
| `artifacts/verify-contact-claim/cue-08-01-fish-0604bbc480.mp3` | Three refusals fired. Zero calls placed after a refusal, measured rather than asserted. |
| `artifacts/verify-contact-claim/cue-08-02-fish-24cc23cb25.mp3` | Six records appended and six outcomes recomputed from the stored evidence. |
| `artifacts/verify-contact-claim/cue-09-00-fish-b4eeee3892.mp3` | Verify re-links the chain and recomputes every outcome with the functions that ran live. |
| `artifacts/verify-contact-claim/cue-09-01-fish-00faf7b11b.mp3` | So take that record and rewrite one stored verdict by hand, from refused to confirmed. |
| `artifacts/verify-contact-claim/cue-09-02-fish-1e59a8b84c.mp3` | It fails twice over. The hash no longer matches. The verdict no longer follows from the evidence. |
| `artifacts/verify-contact-claim/cue-10-00-fish-418ddab0f0.mp3` | One hundred and seventy two tests pass. Five outcomes, three refusals plus a record that fails when it is edited. |
| `artifacts/verify-contact-claim/cue-10-01-fish-3bfc34d3a0.mp3` | There is no CALL-E account yet, so no live call has been placed from this branch. Every number is a reserved example. |

## zeroclaw-solana-bounty

20 cues, 2094 characters.

| file | line |
| --- | --- |
| `artifacts/zeroclaw-solana-bounty/cue-00-00-fish-6cc6798815.mp3` | An agent that can pay a supplier can be talked into paying someone else. So signing sits on the far side of a line these tools cannot cross. |
| `artifacts/zeroclaw-solana-bounty/cue-01-00-fish-fd0b3e5e74.mp3` | A shop wants an agent to pay supplier invoices. Put a key in that agent and every message it reads is a payment instruction. |
| `artifacts/zeroclaw-solana-bounty/cue-01-01-fish-99bdb584c5.mp3` | A better prompt is not a fix. The attacker writes text too. |
| `artifacts/zeroclaw-solana-bounty/cue-02-00-fish-ef77f56815.mp3` | The operator sets the policy once in the host: one allowlisted supplier, a cap, an https endpoint. |
| `artifacts/zeroclaw-solana-bounty/cue-02-01-fish-42f5c87446.mp3` | The owner signs from their own wallet hours later, because a durable nonce keeps those bytes valid. |
| `artifacts/zeroclaw-solana-bounty/cue-03-00-fish-b757968698.mp3` | Here it is on Telegram. The owner asks in plain words. |
| `artifacts/zeroclaw-solana-bounty/cue-03-01-fish-b4e16ea37f.mp3` | What comes back is an unsigned transaction, plus a sentence saying nothing moves until the owner signs. |
| `artifacts/zeroclaw-solana-bounty/cue-04-00-fish-ee32ab099a.mp3` | One command runs the repository's own gate. Two hundred and seventy three test executions across three components, one hundred and sixty one distinct. |
| `artifacts/zeroclaw-solana-bounty/cue-04-01-fish-2b00bb730e.mp3` | Every component's size and digest, printed by the run that built them. |
| `artifacts/zeroclaw-solana-bounty/cue-05-00-fish-73d95e2018.mp3` | Three of the eighteen scenarios build a transaction. Three hundred and sixty eight bytes, a signature slot of sixty four zeros, then the message. |
| `artifacts/zeroclaw-solana-bounty/cue-06-00-fish-c02015b9b7.mp3` | Nine of the eighteen refuse. This recipient is not on the operator's allowlist, so nothing was built. |
| `artifacts/zeroclaw-solana-bounty/cue-06-01-fish-47a8592ff0.mp3` | Seven of those nine refuse with a measured zero RPC calls. Fail closed before the network, not after it. |
| `artifacts/zeroclaw-solana-bounty/cue-07-00-fish-f6ee3144e3.mp3` | A component can only do what its imports allow. That is WebAssembly's rule, not our claim. |
| `artifacts/zeroclaw-solana-bounty/cue-07-01-fish-c64166beee.mp3` | No filesystem, no sockets. It cannot open a keypair file. Not does not, cannot. |
| `artifacts/zeroclaw-solana-bounty/cue-08-00-fish-535487f174.mp3` | That proves it cannot go looking for a key. It does not prove one cannot be handed to it. |
| `artifacts/zeroclaw-solana-bounty/cue-08-01-fish-4573fcf2da.mp3` | Ed25519 is defined in terms of SHA-512. There is none here. SHA-256 is present where address derivation needs it, so that zero means something. |
| `artifacts/zeroclaw-solana-bounty/cue-09-00-fish-249288e4cc.mp3` | A wall of green only proves the checks ran. So every one is broken on purpose, on a throwaway copy. |
| `artifacts/zeroclaw-solana-bounty/cue-09-01-fish-f2082c5332.mp3` | Nine controls, nine checks red. A check nobody has watched fail is decoration. |
| `artifacts/zeroclaw-solana-bounty/cue-10-00-fish-775bbd518e.mp3` | Eighteen scenarios, three unsigned transactions, nine refusals. The whole run diffed against a committed golden file. |
| `artifacts/zeroclaw-solana-bounty/cue-11-00-fish-c1dd517d60.mp3` | Nothing in these three components can sign or broadcast. That is seven checks on the shipped bytes, plus nine controls that make every one of them fail. |
