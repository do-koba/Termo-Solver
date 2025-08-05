from termo import Termo


if __name__ == "__main__":
    termo = Termo(logging=True)
    while True:
        res = termo.dueto()
        print(res, len(res))
