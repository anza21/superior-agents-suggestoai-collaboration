# Superior Agents

## Εξαρτήσεις για Affiliate Product Promoter Agent

- google-auth
- google-auth-oauthlib
- facebook-sdk *(Σημείωση: Το Facebook/Instagram API δεν λειτουργεί ακόμα λόγω αδειοδότησης. Προτείνεται να δοκιμάσετε πρώτα Blogger, Medium, Dev.to, Hashnode, Twitter, LinkedIn, YouTube.)*
- linkedin-v2
- tweepy
- huggingface_hub
- ebaysdk
- moviepy
- TTS
- ffmpeg *(system dependency: apt install ffmpeg ή brew install ffmpeg)*

Βεβαιωθείτε ότι έχετε συμπληρώσει σωστά το `.env` με όλα τα απαραίτητα API keys/tokens για κάθε πλατφόρμα.

## Demo Εκτέλεσης Affiliate Product Promoter Agent (Mock)

Για να δοκιμάσετε τον autonomous affiliate promoter agent με mock δεδομένα:

```bash
cd agent
python scripts/run_affiliate_promoter_mock.py
```

### Τι κάνει το demo;
- Τρέχει 2 κύκλους της πλήρους ροής (discovery, content, video, publishing, enrichment, RAG save) με mock δεδομένα.
- Θα δείτε logs για κάθε βήμα, τα value features, και τα mock αποτελέσματα δημοσίευσης.
- Δεν απαιτούνται πραγματικά API keys/tokens για το demo.

### Περιγραφή Ροής
1. **Ανακάλυψη προϊόντων** (mock eBay, AliExpress, Amazon)
2. **Δημιουργία περιεχομένου** (blog, πίνακας, Q&A) με enrichment value features
3. **Δημιουργία βίντεο** (YouTube script, TTS, video) με enrichment value features
4. **Δημοσίευση** σε Dev.to, Medium, Twitter, LinkedIn, YouTube (mock)
5. **Αποθήκευση** όλων των βημάτων σε mock RAG
6. **Αυτόνομη λειτουργία** (μπορεί να τρέχει σε loop)

### Επόμενα βήματα
- Μπορείτε να αντικαταστήσετε τα mock με πραγματικά API integrations όταν έχετε τα tokens.
- Δείτε τα logs για να καταλάβετε τη ροή και τα δεδομένα που παράγονται.
