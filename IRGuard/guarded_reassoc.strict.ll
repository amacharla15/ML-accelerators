; ModuleID = 'guarded_reassoc.cu'
source_filename = "guarded_reassoc.cu"
target datalayout = "e-p6:32:32-i64:64-i128:128-v16:16-v32:32-n16:32:64"
target triple = "nvptx64-nvidia-cuda"

; Function Attrs: mustprogress nofree noinline norecurse nosync nounwind willreturn memory(argmem: readwrite)
define dso_local ptx_kernel void @guarded_reassoc(ptr noundef readonly captures(none) %0, ptr noundef readonly captures(none) %1, ptr noundef readonly captures(none) %2, ptr noundef readonly captures(none) %3, ptr noundef writeonly captures(none) %4, i32 noundef %5) local_unnamed_addr #0 {
  %7 = tail call noundef i32 @llvm.nvvm.read.ptx.sreg.ctaid.x()
  %8 = tail call noundef i32 @llvm.nvvm.read.ptx.sreg.ntid.x()
  %9 = mul i32 %7, %8
  %10 = tail call noundef i32 @llvm.nvvm.read.ptx.sreg.tid.x()
  %11 = add i32 %9, %10
  %12 = icmp slt i32 %11, %5
  br i1 %12, label %13, label %31

13:                                               ; preds = %6
  %14 = sext i32 %11 to i64
  %15 = getelementptr inbounds float, ptr %0, i64 %14
  %16 = load float, ptr %15, align 4, !tbaa !8
  %17 = fcmp uno float %16, 0.000000e+00
  br i1 %17, label %28, label %18

18:                                               ; preds = %13
  %19 = getelementptr inbounds float, ptr %1, i64 %14
  %20 = load float, ptr %19, align 4, !tbaa !8
  %21 = fmul float %16, %20
  %22 = getelementptr inbounds float, ptr %2, i64 %14
  %23 = load float, ptr %22, align 4, !tbaa !8
  %24 = fadd float %21, %23
  %25 = getelementptr inbounds float, ptr %3, i64 %14
  %26 = load float, ptr %25, align 4, !tbaa !8
  %27 = fadd float %24, %26
  br label %28

28:                                               ; preds = %13, %18
  %29 = phi float [ %27, %18 ], [ 0.000000e+00, %13 ]
  %30 = getelementptr inbounds float, ptr %4, i64 %14
  store float %29, ptr %30, align 4, !tbaa !8
  br label %31

31:                                               ; preds = %28, %6
  ret void
}

; Function Attrs: mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare noundef range(i32 0, 2147483647) i32 @llvm.nvvm.read.ptx.sreg.ctaid.x() #1

; Function Attrs: mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare noundef range(i32 1, 1025) i32 @llvm.nvvm.read.ptx.sreg.ntid.x() #1

; Function Attrs: mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare noundef range(i32 0, 1024) i32 @llvm.nvvm.read.ptx.sreg.tid.x() #1

attributes #0 = { mustprogress nofree noinline norecurse nosync nounwind willreturn memory(argmem: readwrite) "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="sm_89" "target-features"="+ptx84,+sm_89" "uniform-work-group-size"="true" }
attributes #1 = { mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0, !1, !2, !3}
!nvvm.annotations = !{!4}
!llvm.ident = !{!5, !6}
!nvvmir.version = !{!7}

!0 = !{i32 2, !"SDK Version", [2 x i32] [i32 12, i32 4]}
!1 = !{i32 1, !"wchar_size", i32 4}
!2 = !{i32 4, !"nvvm-reflect-ftz", i32 0}
!3 = !{i32 7, !"frame-pointer", i32 2}
!4 = !{ptr @guarded_reassoc}
!5 = !{!"Ubuntu clang version 21.1.8 (++20251221032842+2078da43e25a-1~exp1~20251221153008.77)"}
!6 = !{!"clang version 3.8.0 (tags/RELEASE_380/final)"}
!7 = !{i32 2, i32 0}
!8 = !{!9, !9, i64 0}
!9 = !{!"float", !10, i64 0}
!10 = !{!"omnipotent char", !11, i64 0}
!11 = !{!"Simple C++ TBAA"}
