"""
seeds.py -- Tohum (seed) makaleler ve sentetik uretim sozlukleri.

Buradaki tohum makaleler, alaninda *cok iyi bilinen* gercek yayinlardir.
DOI alanlari kasitli olarak bos birakilmistir: build_dataset.py calistirildiginda
CrossRef API'sinden otoritatif (dogrulanmis) DOI ve metadata cekilir. Boylece
bu dosyaya elle DOI yazip yanlislik (halusinasyon!) ekleme riski ortadan kalkar.

NOT: Bu liste, internet erisimi olmadan da calisabilen "offline ornek veri kumesi"
uretebilmek icin kullanilir. Tam 300 ornekluk resmi veri kumesi, build_dataset.py
ile (internet + API) olusturulur ve annotation_tool.py ile elle dogrulanir.
"""

# (baslik, yazarlar, yil, yayin yeri/dergi)  -- DOI runtime'da CrossRef'ten doldurulur
SEED_PAPERS = [
    # --- Makine ogrenmesi / NLP klasikleri ---
    ("Attention Is All You Need",
     ["A. Vaswani", "N. Shazeer", "N. Parmar", "J. Uszkoreit"], 2017,
     "Advances in Neural Information Processing Systems (NeurIPS)"),
    ("BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
     ["J. Devlin", "M.-W. Chang", "K. Lee", "K. Toutanova"], 2019,
     "Proc. NAACL-HLT"),
    ("Deep Residual Learning for Image Recognition",
     ["K. He", "X. Zhang", "S. Ren", "J. Sun"], 2016,
     "Proc. IEEE Conf. on Computer Vision and Pattern Recognition (CVPR)"),
    ("Generative Adversarial Nets",
     ["I. Goodfellow", "J. Pouget-Abadie", "M. Mirza", "B. Xu"], 2014,
     "Advances in Neural Information Processing Systems (NeurIPS)"),
    ("Adam: A Method for Stochastic Optimization",
     ["D. P. Kingma", "J. Ba"], 2015,
     "Proc. Int. Conf. on Learning Representations (ICLR)"),
    ("ImageNet Classification with Deep Convolutional Neural Networks",
     ["A. Krizhevsky", "I. Sutskever", "G. E. Hinton"], 2012,
     "Advances in Neural Information Processing Systems (NeurIPS)"),
    ("Language Models are Few-Shot Learners",
     ["T. B. Brown", "B. Mann", "N. Ryder", "M. Subbiah"], 2020,
     "Advances in Neural Information Processing Systems (NeurIPS)"),
    ("Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
     ["P. Lewis", "E. Perez", "A. Piktus", "F. Petroni"], 2020,
     "Advances in Neural Information Processing Systems (NeurIPS)"),
    ("Sequence to Sequence Learning with Neural Networks",
     ["I. Sutskever", "O. Vinyals", "Q. V. Le"], 2014,
     "Advances in Neural Information Processing Systems (NeurIPS)"),
    ("Long Short-Term Memory",
     ["S. Hochreiter", "J. Schmidhuber"], 1997,
     "Neural Computation"),
    ("Distributed Representations of Words and Phrases and their Compositionality",
     ["T. Mikolov", "I. Sutskever", "K. Chen", "G. Corrado"], 2013,
     "Advances in Neural Information Processing Systems (NeurIPS)"),
    ("Dropout: A Simple Way to Prevent Neural Networks from Overfitting",
     ["N. Srivastava", "G. Hinton", "A. Krizhevsky", "I. Sutskever"], 2014,
     "Journal of Machine Learning Research (JMLR)"),
    # --- Siber guvenlik klasikleri ---
    ("Spectre Attacks: Exploiting Speculative Execution",
     ["P. Kocher", "J. Horn", "A. Fogh", "D. Genkin"], 2019,
     "Proc. IEEE Symposium on Security and Privacy (S&P)"),
    ("Meltdown: Reading Kernel Memory from User Space",
     ["M. Lipp", "M. Schwarz", "D. Gruss", "T. Prescher"], 2018,
     "Proc. USENIX Security Symposium"),
    ("Understanding the Mirai Botnet",
     ["M. Antonakakis", "T. April", "M. Bailey", "M. Bernhard"], 2017,
     "Proc. USENIX Security Symposium"),
    ("The Matter of Heartbleed",
     ["Z. Durumeric", "F. Li", "J. Kasten", "J. Amann"], 2014,
     "Proc. ACM Internet Measurement Conference (IMC)"),
    ("Intriguing Properties of Neural Networks",
     ["C. Szegedy", "W. Zaremba", "I. Sutskever", "J. Bruna"], 2014,
     "Proc. Int. Conf. on Learning Representations (ICLR)"),
    ("Explaining and Harnessing Adversarial Examples",
     ["I. J. Goodfellow", "J. Shlens", "C. Szegedy"], 2015,
     "Proc. Int. Conf. on Learning Representations (ICLR)"),
    ("Practical Black-Box Attacks against Machine Learning",
     ["N. Papernot", "P. McDaniel", "I. Goodfellow", "S. Jha"], 2017,
     "Proc. ACM Asia Conf. on Computer and Communications Security (ASIACCS)"),
    ("Membership Inference Attacks Against Machine Learning Models",
     ["R. Shokri", "M. Stronati", "C. Song", "V. Shmatikov"], 2017,
     "Proc. IEEE Symposium on Security and Privacy (S&P)"),
]

# H1 (var olmayan referans) sentezi icin sozlukler -----------------------------
FAKE_SURNAMES = [
    "Anderson", "Bryant", "Castillo", "Delgado", "Esposito", "Fairchild",
    "Grimaldi", "Halloran", "Iverson", "Janssen", "Kowalski", "Lindqvist",
    "Marchetti", "Novikov", "Okafor", "Pettersson", "Quintana", "Rasmussen",
    "Saltykov", "Tanaka", "Underwood", "Vasquez", "Whitmore", "Yamamoto",
]
FAKE_INITIALS = ["A.", "B.", "C.", "D.", "E.", "F.", "G.", "H.", "J.", "K.",
                 "L.", "M.", "N.", "P.", "R.", "S.", "T."]

FAKE_TITLE_PREFIX = [
    "A Unified Framework for", "Towards Robust", "Scalable",
    "Deep Learning for", "Adversarial", "Self-Supervised",
    "Federated", "Explainable", "Graph-Based", "Probabilistic",
    "Real-Time", "Privacy-Preserving", "Hierarchical", "End-to-End",
]
FAKE_TITLE_TOPIC = [
    "Intrusion Detection in IoT Networks",
    "Malware Classification using Transformers",
    "Phishing URL Detection",
    "Side-Channel Leakage Quantification",
    "Vulnerability Severity Prediction",
    "Encrypted Traffic Analysis",
    "Insider Threat Detection",
    "Ransomware Behavior Modeling",
    "Zero-Day Exploit Forecasting",
    "Botnet Command-and-Control Identification",
    "Anomaly Detection in SIEM Logs",
    "Automated CVSS Score Assessment",
    "Supply-Chain Attack Attribution",
    "Adversarial Robustness of Spam Filters",
]
FAKE_VENUES = [
    "Proc. IEEE Symposium on Security and Privacy (S&P)",
    "Proc. USENIX Security Symposium",
    "Proc. ACM Conf. on Computer and Communications Security (CCS)",
    "Proc. Network and Distributed System Security Symposium (NDSS)",
    "IEEE Transactions on Information Forensics and Security",
    "Computers & Security",
    "Proc. Annual Computer Security Applications Conference (ACSAC)",
    "Journal of Cybersecurity",
]

# H3 (semantik uyumsuzluk) icin alakasiz "atif baglami" cumleleri --------------
UNRELATED_CONTEXTS = [
    "The authors propose a novel reinforcement-learning controller for "
    "autonomous drone navigation in GPS-denied indoor environments.",
    "This work investigates the thermodynamic properties of perovskite "
    "solar cells under high-temperature operating conditions.",
    "We present a longitudinal epidemiological study on cardiovascular "
    "disease risk factors in a rural population.",
    "The paper introduces a finite-element model for predicting fatigue "
    "fractures in titanium aerospace components.",
    "Our contribution is a phonological analysis of vowel shifts in "
    "Medieval English manuscripts.",
    "This study evaluates the carbon-sequestration capacity of mangrove "
    "forests across three coastal regions.",
]
