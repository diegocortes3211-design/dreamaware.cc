package common

import (
	"context"
	"crypto/tls"

	"github.com/spiffe/go-spiffe/v2/spiffeid"
	"github.com/spiffe/go-spiffe/v2/spiffetls/tlsconfig"
	"github.com/spiffe/go-spiffe/v2/workloadapi"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
)

func MTLSClientConn(ctx context.Context, addr, expectedServerID string) (*grpc.ClientConn, error) {
	source, err := workloadapi.NewX509Source(ctx)
	if err != nil {
		return nil, err
	}
	defer source.Close()

	id, err := spiffeid.FromString(expectedServerID)
	if err != nil {
		return nil, err
	}

	tlsConf := &tls.Config{
		MinVersion: tls.VersionTLS13,
		GetClientCertificate: tlsconfig.GetClientCertificate(source),
		VerifyPeerCertificate: tlsconfig.VerifyPeerCertificate(
			tlsconfig.AuthorizeID(id),
		),
	}
	return grpc.DialContext(ctx, addr, grpc.WithTransportCredentials(credentials.NewTLS(tlsConf)))
}