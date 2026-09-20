// Canned sample data for MockApiClient, shaped exactly like BRAIN.md
// Section F (Shared Data Models). This is NOT authoritative seed data —
// the real `data/seed/` files (Dipanshu / Saloni Sharma's loaders) are the
// source of truth once the backend exists. This file exists only so the
// frontend can be developed and demoed in isolation, and so its shape
// matches what the real backend will return closely enough that swapping
// USE_MOCK_API to false is a config change, not a rewrite.
//
// snake_case field names match BRAIN.md exactly on purpose.

export const touchpoints = [
  {
    touchpoint_id: '11111111-1111-4111-8111-111111111111',
    name: 'Rajkiya Uchcha Vidyalaya, Bhaderwah',
    type: 'school',
    village: 'Bhaderwah',
    state: 'Jammu and Kashmir',
    pickup_address: 'Rajkiya Uchcha Vidyalaya, Main Bazaar Road, Bhaderwah, Doda, J&K 182222',
    admin_user_id: 'admin-001'
  },
  {
    touchpoint_id: 't-002',
    name: 'Common Service Centre, Channapatna',
    type: 'csc',
    village: 'Channapatna',
    state: 'Karnataka',
    pickup_address: 'CSC Channapatna, Bengaluru-Mysuru Highway, Channapatna, Karnataka 562160',
    admin_user_id: 'admin-002'
  },
  {
    touchpoint_id: 't-003',
    name: 'Common Service Centre, Pochampally',
    type: 'csc',
    village: 'Pochampally',
    state: 'Telangana',
    pickup_address: 'CSC Pochampally, Yadadri Bhuvanagiri District, Telangana 508284',
    admin_user_id: 'admin-003'
  }
];

export const sellers = [
  {
    seller_id: 's-001',
    name: 'Meena Devi',
    village: 'Bhaderwah',
    state: 'Jammu and Kashmir',
    seller_language: 'hi',
    phone: '+91-9XXXX-11111',
    touchpoint_id: '11111111-1111-4111-8111-111111111111',
    created_at: '2026-08-01T05:30:00Z'
  },
  {
    seller_id: 's-002',
    name: 'Krishnappa Gowda',
    village: 'Channapatna',
    state: 'Karnataka',
    seller_language: 'hi',
    phone: '+91-9XXXX-22222',
    touchpoint_id: 't-002',
    created_at: '2026-08-03T06:15:00Z'
  },
  {
    seller_id: 's-003',
    name: 'Lakshmi Yadav',
    village: 'Pochampally',
    state: 'Telangana',
    seller_language: 'hi',
    phone: '+91-9XXXX-33333',
    touchpoint_id: 't-003',
    created_at: '2026-08-05T07:00:00Z'
  }
];

export const products = [
  {
    product_id: 'p-001',
    seller_id: 's-001',
    category: 'textile',
    raw_description: 'Hum bhed ke oon se haath se bune huye gaane garam shawl banate hain, humare gaon mein sardi bahut hoti hai',
    seller_language: 'hi',
    created_at: '2026-08-01T05:40:00Z'
  },
  {
    product_id: 'p-002',
    seller_id: 's-002',
    category: 'toy',
    raw_description: 'Hum lakdi ke rangeen gudiya aur khilaune banate hain, yeh Channapatna ki purani kala hai',
    seller_language: 'hi',
    created_at: '2026-08-03T06:30:00Z'
  },
  {
    product_id: 'p-003',
    seller_id: 's-003',
    category: 'textile',
    raw_description: 'Hum Pochampally Ikat saree banate hain, dhaage ko pehle rangte hain fir bunte hain',
    seller_language: 'hi',
    created_at: '2026-08-05T07:10:00Z'
  }
];

export const listings = [
  {
    listing_id: 'l-001',
    product_id: 'p-001',
    category: 'textile',
    listing_title: 'Handwoven Wool Shawl from Bhaderwah',
    description_en:
      'A soft, hand-spun wool shawl woven on a traditional pit loom in the mountain town of Bhaderwah. Each shawl takes several days to complete and uses wool sourced from local sheep, prized for its warmth in the Himalayan winter.',
    description_local:
      'Bhaderwah ke pahadi ilaake mein haath se katee gayi oon se, parampaagat loom par bunaa gaya narm shawl. Ise banane mein kai din lagte hain aur yeh sthaniya bhed ki oon se bana hai.',
    price_suggestion: 2200,
    photo_guidance: [
      'Shoot in daylight, near a window',
      'Lay the shawl flat to show the full weave pattern',
      'Show the texture close-up in one photo',
      'Include a size reference like a coin or ruler'
    ],
    story:
      'Meena Devi has been weaving wool shawls for over twenty years, a skill passed down from her mother. A portion of proceeds from this sale, at her own choice, supports her local school.',
    compliance_flags: [],
    review_status: 'approved',
    created_at: '2026-08-01T06:00:00Z'
  },
  {
    listing_id: 'l-002',
    product_id: 'p-002',
    category: 'toy',
    listing_title: 'Channapatna Wooden Hand-Painted Toy Set',
    description_en:
      'Vibrant, lacquer-finished wooden toys from Channapatna, a craft tradition over 200 years old. Made from sustainably sourced ivory wood and finished with natural vegetable dyes, safe for children.',
    description_local:
      'Channapatna ki 200 saal purani parampara se bane rangeen lakdi ke khilaune. Yeh prakritik rangon se rangeen kiye gaye hain aur bachchon ke liye surakshit hain.',
    price_suggestion: 850,
    photo_guidance: [
      'Shoot against a plain, light background',
      'Show all colors in the set together',
      'Include one photo of the toy in a child\u2019s hand for scale'
    ],
    story: null,
    compliance_flags: [],
    review_status: 'approved',
    created_at: '2026-08-03T07:00:00Z'
  },
  {
    listing_id: 'l-003',
    product_id: 'p-003',
    category: 'textile',
    listing_title: 'Pochampally Ikat Silk Saree',
    description_en:
      'A traditional Ikat saree from Pochampally, Telangana, where the yarn is tie-dyed before weaving to create the signature blurred geometric pattern. A single saree can take up to two weeks to weave.',
    description_local:
      'Pochampally, Telangana ki paramparik Ikat saree, jisme dhaage ko bunai se pehle bandh kar rangaa jaata hai. Ek saree banane mein do hafte tak lag sakte hain.',
    price_suggestion: 4500,
    photo_guidance: [
      'Shoot in natural light to show true colors',
      'Photograph the saree both folded and draped',
      'Include a close-up of the Ikat pattern edge'
    ],
    story:
      'Lakshmi Yadav learned Ikat weaving from her grandmother. She has opted to route a share of her proceeds to her village CSC\u2019s development fund.',
    compliance_flags: [],
    review_status: 'approved',
    created_at: '2026-08-05T08:00:00Z'
  }
];

export const contributions = [
  {
    contribution_id: 'c-001',
    seller_id: 's-001',
    opted_in: true,
    percentage: 10,
    touchpoint_id: '11111111-1111-4111-8111-111111111111',
    updated_at: '2026-08-01T06:05:00Z'
  },
  {
    contribution_id: 'c-002',
    seller_id: 's-002',
    opted_in: false,
    percentage: 0,
    touchpoint_id: 't-002',
    updated_at: '2026-08-03T07:05:00Z'
  },
  {
    contribution_id: 'c-003',
    seller_id: 's-003',
    opted_in: true,
    percentage: 15,
    touchpoint_id: 't-003',
    updated_at: '2026-08-05T08:05:00Z'
  }
];

export const ledgerEntries = [];

export const onboardingScript = {
  idea: {
    nextStage: 'procedure',
    reply:
      'Namaste! Main aapko Kalaa Setu ke baare mein bataata hoon — yeh Amazon se juda ek tarika hai jisse aap apna saamaan poori duniya mein bech sakte hain, bina angrezi jaane. Pehle mujhe bataiye, aap kya banate hain?'
  },
  procedure: {
    nextStage: 'business_model',
    reply:
      'Bahut badhiya! Ab main aapko poori prakriya samjhaata hoon: aap apna saamaan apne school/CSC par layenge, main aapse kuch sawal poochhunga, aur fir ek listing taiyaar hogi. Koi delivery ki chinta nahi — saamaan yahin se uthaya jaayega.'
  },
  business_model: {
    nextStage: 'capture',
    reply:
      'Ab paison ki baat: jo bhi bikri hogi, uska paisa seedha aapko milega, ek chhota Amazon shulk katkar. Aap yeh bhi chun sakte hain (bilkul optional hai) ki apni kamai ka kuch hissa apne school/CSC ke vikaas fund mein bhejna chahte hain ya nahi.'
  },
  capture: {
    nextStage: 'done',
    reply:
      'Shukriya! Maine aapki jaankari nithaar li hai — ab main iska ek professional listing draft banaata hoon jise aap dekh sakte hain.'
  }
};

