for i in {1..$1} 
do
    curl -d username=test$i localhost:8080/adduser
done
