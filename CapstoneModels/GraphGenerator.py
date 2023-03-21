import matplotlib.pyplot as plt

def generate_tokens_length(distribution: dict):
    x_val = list(distribution.keys())
    y_val = list(distribution.values())
    plt.bar(x_val, y_val)

    plt.xlabel('Token Length')
    plt.ylabel('Appears')
    plt.title('Token Length Graph')

    plt.show()