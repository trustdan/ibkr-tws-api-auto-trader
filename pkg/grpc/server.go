package grpc

import (
	"context"
	"log"
	"net"

	"github.com/user/trader-scanner/pkg/pb"
	"github.com/user/trader-scanner/pkg/scan"
	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
)

// ScannerServer implements the gRPC ScannerService
type ScannerServer struct {
	pb.UnimplementedScannerServiceServer
	processor *scan.Processor
}

// NewScannerServer creates a new ScannerServer with the provided processor
func NewScannerServer(processor *scan.Processor) *ScannerServer {
	return &ScannerServer{
		processor: processor,
	}
}

// ScanUniverse implements the ScanUniverse RPC method
func (s *ScannerServer) ScanUniverse(ctx context.Context, req *pb.ScanRequest) (*pb.ScanResponse, error) {
	log.Printf("Received ScanUniverse request with %d symbols", len(req.Symbols))

	// If specific symbols are provided, temporarily override the universe
	originalUniverse := s.processor.Config.Universe
	if len(req.Symbols) > 0 {
		s.processor.Config.Universe = req.Symbols
		defer func() {
			// Restore the original universe when done
			s.processor.Config.Universe = originalUniverse
		}()
	}

	// Perform the scan
	results, err := s.processor.ScanAll(ctx)
	if err != nil {
		log.Printf("Error in scan: %v", err)
		return nil, err
	}

	// Convert scan results to protobuf response
	resp := &pb.ScanResponse{
		Results: make([]*pb.ScanResponse_Result, 0, len(results)),
	}

	// Map string signal types to protobuf enum
	signalTypeMap := map[string]pb.SignalType{
		scan.SignalNone:       pb.SignalType_NONE,
		scan.SignalCallDebit:  pb.SignalType_CALL_DEBIT,
		scan.SignalPutDebit:   pb.SignalType_PUT_DEBIT,
		scan.SignalCallCredit: pb.SignalType_CALL_CREDIT,
		scan.SignalPutCredit:  pb.SignalType_PUT_CREDIT,
	}

	for _, r := range results {
		signalType, ok := signalTypeMap[r.SignalType]
		if !ok {
			signalType = pb.SignalType_NONE
		}

		resp.Results = append(resp.Results, &pb.ScanResponse_Result{
			Symbol: r.Symbol,
			Signal: signalType,
		})
	}

	log.Printf("Returning %d scan results", len(resp.Results))
	return resp, nil
}

// StartServer starts the gRPC server on the specified address
func StartServer(addr string, processor *scan.Processor) (*grpc.Server, error) {
	lis, err := net.Listen("tcp", addr)
	if err != nil {
		log.Printf("Failed to listen on %s: %v", addr, err)
		return nil, err
	}

	// Create a new gRPC server
	server := grpc.NewServer()

	// Register the scanner service
	scannerServer := NewScannerServer(processor)
	pb.RegisterScannerServiceServer(server, scannerServer)

	// Enable reflection for debugging
	reflection.Register(server)

	// Start the server in a goroutine
	go func() {
		log.Printf("Starting gRPC server on %s", addr)
		if err := server.Serve(lis); err != nil {
			log.Fatalf("Failed to serve: %v", err)
		}
	}()

	return server, nil
}
