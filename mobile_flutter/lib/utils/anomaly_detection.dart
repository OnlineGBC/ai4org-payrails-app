// Extracted from consumer_pay_confirm_screen so that anomaly logic can be
// unit-tested independently of the Flutter widget tree.

const Set<String> kDangerousKeywords = {
  'nuclear', 'weapon', 'missile', 'explosive', 'bomb', 'grenade',
  'fentanyl', 'cocaine', 'heroin', 'meth', 'drug', 'narcotics',
  'illegal', 'stolen', 'counterfeit', 'smuggle', 'launder',
};

const Map<String, String> kMerchantCategory = {
  'westernunion': 'money_transfer',
  'netflix': 'streaming',
  'boostmobile': 'telecom',
  'foodlion': 'grocery',
  'aldi': 'grocery',
  'costco': 'grocery',
  'walmart': 'grocery',
  'dollargeneral': 'grocery',
  'mcdonalds': 'restaurant',
  'burgerking': 'restaurant',
  'subway': 'restaurant',
  'target': 'retail',
  'nike': 'retail',
};

const Set<String> kPhysicalGoodsKeywords = {
  'toothpaste', 'groceries', 'grocery', 'shoes', 'burger', 'sandwich',
  'meal', 'food', 'clothing', 'clothes', 'shirt', 'pants', 'dress',
  'hardware', 'furniture', 'electronics', 'appliance',
};

const Set<String> kFinancialKeywords = {
  'transfer', 'remittance', 'wire', 'send money', 'money order',
  'cash', 'loan', 'payment plan', 'investment',
};

/// Returns a warning string if the [description] looks anomalous for the
/// given [merchantName], or null if the transaction looks normal.
String? checkAnomaly(String merchantName, String description) {
  final descLower = description.toLowerCase();

  // Universal dangerous keyword check — runs before any category logic
  for (final kw in kDangerousKeywords) {
    if (descLower.contains(kw)) {
      return '⚠️ Suspicious description detected: "$description" — this transaction may violate policies. '
          'Proceed only if you are certain this is legitimate.';
    }
  }

  final merchantLower = merchantName.toLowerCase().replaceAll(' ', '');

  String? category;
  for (final entry in kMerchantCategory.entries) {
    if (merchantLower.contains(entry.key)) {
      category = entry.value;
      break;
    }
  }
  if (category == null) return null;

  if (category == 'money_transfer') {
    for (final kw in kPhysicalGoodsKeywords) {
      if (descLower.contains(kw)) {
        return 'Unusual description for a money transfer merchant. '
            '"$description" sounds like a physical purchase. '
            'Proceed only if this is intentional.';
      }
    }
  }

  if (category == 'streaming' || category == 'telecom') {
    for (final kw in kPhysicalGoodsKeywords) {
      if (descLower.contains(kw)) {
        return 'Unusual description for a ${category == 'streaming' ? 'streaming' : 'telecom'} merchant. '
            '"$description" sounds like a physical purchase. '
            'Proceed only if this is intentional.';
      }
    }
  }

  if (category == 'restaurant' || category == 'grocery' || category == 'retail') {
    for (final kw in kFinancialKeywords) {
      if (descLower.contains(kw)) {
        return 'Unusual description for a $category merchant. '
            '"$description" sounds like a financial transaction. '
            'Proceed only if this is intentional.';
      }
    }
  }

  return null;
}
