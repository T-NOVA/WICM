sudo watch -n1 '
echo "s1:" &&
ovs-ofctl dump-flows s1 &&
echo &&
echo "s2:" &&
ovs-ofctl dump-flows s2 &&
echo &&
echo "NFVI-PoP1:" && 
ovs-ofctl dump-flows s3 &&
echo &&
echo "NFVI-PoP2:" &&
ovs-ofctl dump-flows s4'

