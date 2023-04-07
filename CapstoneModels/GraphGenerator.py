import matplotlib.pyplot as plt

def generate_tokens_length(distribution: dict, name: str = ''):
    x_val = list(distribution.keys())
    y_val = list(distribution.values())
    plt.bar(x_val, y_val)

    plt.xlabel('Token Length')
    plt.ylabel('Appears')
    plt.title(f'Token Length Graph :: {name}')

    plt.show()
    print('show plot')

def generate_distribution(distribution: dict):
    fig, (male, female) = plt.subplots(1, 2, figsize=(10, 5))

    male.plot([k % 10 for k in distribution.keys() if k < 10], [distribution[k] for k in distribution.keys() if k < 10], 'o')
    male.set_title('Male Participant Count')
    male.set_xlabel('Age')
    male.set_ylabel('Appears')

    female.plot([k % 10 for k in distribution.keys() if k >= 10], [distribution[k] for k in distribution.keys() if k >= 10], 'o')
    female.set_title('Female Participant Count')
    female.set_xlabel('Age')
    female.set_ylabel('Appears')

    plt.show()
