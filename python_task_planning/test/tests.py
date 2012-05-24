import roslib; roslib.load_manifest('hip')

def test_cof_entails():
    from hip import ConjunctionOfFluents
    cof1 = ConjunctionOfFluents([])
    cof2 = ConjunctionOfFluents([])
    assert(cof1.entails(cof2))

if __name__ == '__main__':
    test_cof_entails()
