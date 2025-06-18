import pandas as pd

def feat_tax_func(character, feats):
    feat_taxed_dict = {}
    total_feat_tax_dict = character.feat_tax
    feat_tax_data = total_feat_tax_dict.get("feat_tax", {})

    for feat in feats:
        if feat in feat_tax_data:
            feat_taxed_dict[feat] = list(feat_tax_data[feat].values())

    print_taxable_feats(character, feat_taxed_dict)
    return feat_taxed_dict


def confirm_eligible(character, feat_taxed_dict):
    return

def print_taxable_feats(character, feat_taxed_dict):
    taxable_names = []
    feat_data = pd.read_csv(f'{"data/feats.csv"}', sep='|', on_bad_lines='skip')
    feat_names_data = feat_data['name'].tolist()

    for n in feat_names_data:
        if any(keyword in n.lower() for keyword in ("greater", "improved", "extra")):
            taxable_names.append(n)
    print("taxable_names:", taxable_names)