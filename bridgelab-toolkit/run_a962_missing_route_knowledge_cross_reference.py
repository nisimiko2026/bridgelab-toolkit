from bridge.missing_route_knowledge_cross_reference import cross_reference_missing_route_knowledge

def main():
    r=cross_reference_missing_route_knowledge(start_seed=1,count=10000)
    print("A9.6.2 Missing-Route Knowledge Cross-Reference")
    print("runs",r.runs)
    print("missing_route_population",r.missing_route_population)
    print()
    for x in r.entries:
        print(x.family.value, x.population, x.review_classification.value,
              x.knowledge_status.value, "production-ready="+str(x.production_ready).lower())
        print(" ",x.basis)

if __name__=="__main__":
    main()
